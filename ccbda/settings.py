"""
Django settings for ccbda project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
import json
from dotenv import load_dotenv
import requests
import logging

import form.apps

logger = logging.getLogger('django')

def get_metadata(path='', default=''):
    if DEBUG:
        return default
    try:
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "60"}
        response = requests.put('http://169.254.169.254/latest/api/token', headers=headers, timeout=5)
        if response.status_code == 200:
            response = requests.get(f'http://169.254.169.254/latest/meta-data/{path}',
                                    headers={'X-aws-ec2-metadata-token': response.text})
            response.raise_for_status()  # Raises an HTTPError
            return response.text
        else:
            return "unknown"
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error accessing metadata: {e}")
        return default


# Load environment variables from a .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = bool(os.environ.get("DJANGO_DEBUG", default=False))

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS').split(':')
ALLOWED_HOSTS.append(get_metadata('local-ipv4','127.0.0.1'))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'form',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ccbda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ccbda.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}
DATABASE = os.getenv('DATABASE','default')

if DATABASE == "postgresql":
    DATABASES['default'] = {
        "ENGINE": "django.db.backends.postgresql",
        'DISABLE_SERVER_SIDE_CURSORS': True,
        "NAME": os.getenv('DB_NAME', '---no-db-name---'),
        "USER": os.getenv('DB_USER', '---no-db-user---'),
        "PASSWORD": os.getenv('DB_PASSWORD', '---no-db-password---'),
        "HOST": os.getenv('DB_HOST', '127.0.0.1'),
        "PORT": os.getenv('DB_PORT', 5432),
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AWS_EC2_INSTANCE_ID = get_metadata('instance-id','localhost')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} [" + AWS_EC2_INSTANCE_ID + "] [{funcName}:{module}:{lineno}] {message}",
            "style": "{",
        },
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        'file': {
            'level': 'INFO',
            "formatter": "verbose",
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, "file.log"),
            "maxBytes": 5 * 1024,  # 5 K
            "backupCount": 1,
            "encoding": None,
            "delay": False,
        },
        "s3": {
            "level": "INFO",
            "formatter": "verbose",
            "class": "ccbda.S3RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "s3.log"),
            "maxBytes": 1024 ,  # 5 K
            "backupCount": 1,
            "encoding": None,
            "delay": 0,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "s3"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

CCBDA_SIGNUP_TABLE = os.getenv('CCBDA_SIGNUP_TABLE')
AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
AWS_S3_LOGS_PREFIX = os.getenv('AWS_S3_LOGS_PREFIX')

RSS_URLS = [
    'https://www.cloudcomputing-news.net/feed/',
    'https://feeds.feedburner.com/cioreview/fvHK',
    'https://www.techrepublic.com/rssfeeds/topic/cloud/',
    'https://aws.amazon.com/blogs/aws/feed/',
    'https://cloudtweaks.com/feed/',
]