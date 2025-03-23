# logs configuration
import logging.handlers
import boto3
import os
from botocore.exceptions import ClientError
from django.conf import settings
import pathlib
from datetime import datetime, timezone


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
            now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            s3_key = f'{self.logs_prefix}{stem}.{now}{suffix}'

            if os.path.exists(source):
                os.rename(source, dest)
            with open(dest, "rb") as f:
                self.s3_client.upload_fileobj(f, self.bucket_name, s3_key)
            os.remove(dest)


    def emit(self, record):
        try:
            log_data = self.format(record)
            try:
                if self.shouldRollover(record):
                    logging.info(f'ROLLOVER {record.name}')
                    self.doRollover()
                self.stream.write(log_data + self.terminator)
            except Exception as err:
                self.handleError(record)
        except ClientError as e:
            logging.error(f"Error sending log to S3: {e}")
