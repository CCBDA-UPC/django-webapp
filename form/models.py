import boto3
import re
from django.conf import settings
import feedparser
import requests
import logging
from django.db import models
from django.shortcuts import reverse
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup


logger = logging.getLogger('django')

class Feeds(models.Model):
    title = models.CharField(max_length=200)
    link = models.URLField()
    summary = models.TextField()
    author = models.CharField(max_length=120)
    hits = models.BigIntegerField(default=0)

    def refresh_data(self):
        for u in settings.RSS_URLS:
            response = requests.get(u)
            try:
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    article = Feeds.objects.create(
                        title=entry.title,
                        link='',
                        summary='',
                        author=entry.author
                    )
                    base_link = reverse('form:hit', kwargs={'id': article.id})
                    article.link = urljoin(base_link,'?'+urlencode({'url':entry.link}))
                    summary = BeautifulSoup(entry.summary, 'html.parser')
                    for anchor in summary.find_all('a'):
                        anchor['href'] = urljoin(base_link,'?'+urlencode({'url':anchor['href']}))
                        anchor['target'] = '_blank'
                    article.summary = str(summary)
                    article.save()
                    print(entry.title)
            except Exception as e:
                logger.error(f'Feed reading error: {e}')


class Leads():

    def insert_lead(self, name, email, previewAccess):
        try:
            dynamodb = boto3.resource('dynamodb',
                                      region_name=settings.AWS_REGION,
                                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                      aws_session_token=settings.AWS_SESSION_TOKEN)
            table = dynamodb.Table(settings.CCBDA_SIGNUP_TABLE)
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        try:
            response = table.put_item(
                Item={
                    'name': name,
                    'email': email,
                    'preview': previewAccess,
                },
                ReturnValues='ALL_OLD',
            )
        except Exception as e:
            logger.error(
                'Error adding item to database: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        status = response['ResponseMetadata']['HTTPStatusCode']
        if status == 200:
            if 'Attributes' in response:
                logger.info('Existing item updated to database.')
                return 409
            logger.info('New item added to database.')
        else:
            logger.error('Unknown error inserting item to database.')

        return status
