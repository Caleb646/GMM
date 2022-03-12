import os

from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class StaticStorage(S3StaticStorage):
    location = f'static/{os.getenv("AWS_MEDIA_LOCATION_PREFIX", "production")}'
    default_acl = "public-read"


class PrivateFileStorage(S3Boto3Storage):
    location = f'media/{os.getenv("AWS_MEDIA_LOCATION_PREFIX", "production")}'
    default_acl = "private"
    file_overwrite = True
