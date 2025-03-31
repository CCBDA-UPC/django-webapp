import logging.handlers
import boto3
import os
from botocore.exceptions import ClientError
from django.conf import settings
import pathlib
from datetime import datetime, timezone
from elasticsearch import Elasticsearch
import json

logger = logging.getLogger('django')
logger_root = logging.getLogger()


class JsonFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.fmt_dict = kwargs.get('basic', {"message": "message"})
        self.default_time_format = kwargs.get('time_format', "%Y-%m-%dT%H:%M:%S")
        self.default_msec_format = kwargs.get('msec_format', "%s.%03dZ")
        self.datefmt = None
        self.extra = kwargs.get('extra', {})

    def usesTime(self) -> bool:
        # Overwritten to look for the attribute in the format dict values instead of the fmt string.
        return "asctime" in self.fmt_dict.values()

    def formatMessage(self, record) -> dict:
        # Overwritten to return a dictionary of the relevant LogRecord attributes instead of a string.
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record) -> str:
        # Mostly the same as the parent's class method, the difference being that a dict is manipulated and dumped as JSON instead of a string.

        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        message_dict = self.formatMessage(record)

        p = os.path.relpath(record.pathname,settings.BASE_DIR).split('/')
        p.remove(record.filename)
        if 'site-packages' in p:
            add_chunk = False
            app_name = ''
            for item in p:
                if item == 'site-packages':
                    add_chunk = True
                    continue
                if add_chunk:
                    app_name += f'/{item}'
            message_dict['app'] = app_name
        else:
            message_dict['app'] = p[0]

        if isinstance (record.args, dict):
            for k, v in record.args.items():
                message_dict[k] = v

        for k, v in self.extra.items():
            message_dict[k] = v

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(message_dict, default=str)


class ElasticsearchHandler(logging.handlers.BufferingHandler):
    def __init__(self, index="logs", capacity=4):
        # capacity: number of logging records buffered
        super().__init__(capacity=capacity)
        self.es_client = Elasticsearch(cloud_id=settings.ELK_CLOUD_ID, basic_auth=("elastic", settings.ELK_PASSWORD))
        self.index = index

    def emit(self, record):
        log_entry = self.format(record)
        # Send the log entry to Elasticsearch
        self.es_client.index(index=self.index, document=json.loads(log_entry))

    def flush(self):
        for record in self.buffer:
            log_entry = self.format(record)
            # Send the log entry to Elasticsearch
            self.es_client.index(index=self.index, document=json.loads(log_entry))
        self.buffer = []

class S3RotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=0):
        super().__init__(
            filename=filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay
        )
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.logs_prefix = settings.AWS_S3_LOGS_PREFIX
        if not self.logs_prefix.endswith("/"):
            self.logs_prefix += "/"

    def rotate(self, source, dest):
        if callable(self.rotator):
            self.rotator(source, dest)
        else:
            stem = pathlib.Path(source).stem
            suffix = pathlib.Path(source).suffix
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
            s3_key = f'{self.logs_prefix}{stem}.{now}{suffix}'

            if os.path.exists(source):
                os.rename(source, dest)
                if os.stat(dest).st_size > 0:
                    self.s3_client.upload_file(dest, self.bucket_name, s3_key)
                os.remove(dest)

    def emit(self, record):
        try:
            log_data = self.format(record)
            try:
                if self.shouldRollover(record):
                    self.doRollover()
                self.stream.write(log_data + self.terminator)
            except Exception as err:
                self.handleError(record)
        except ClientError as e:
            logger.error(f"Error sending log to S3: {e}")