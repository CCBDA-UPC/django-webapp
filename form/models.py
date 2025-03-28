import boto3
from django.conf import settings
import logging
from django.db import models


class Feeds(models.Model):
    title = models.CharField(max_length=200)
    link = models.URLField()
    summary = models.TextField()
    author = models.CharField(max_length=120)
    hits = models.BigIntegerField(default=0)


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
            logging.error(
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
            logging.error(
                'Error adding item to database: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        status = response['ResponseMetadata']['HTTPStatusCode']
        if status == 200:
            if 'Attributes' in response:
                logging.info('Existing item updated to database.')
                return 409
            logging.info('New item added to database.')
        else:
            logging.error('Unknown error inserting item to database.')

        return status
