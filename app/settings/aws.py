import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Boto3
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
print("\nSettings: using AWS file storage\n")
STATICFILES_STORAGE = 'rfis.storage_backends.StaticStorage'
# AWS
AWS_S3_ACCESS_KEY_ID = os.environ["AWS_S3_ACCESS_KEY_ID"]
AWS_S3_SECRET_ACCESS_KEY = os.environ["AWS_S3_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
#AWS_DEFAULT_ACL = 'public-read'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
# A path prefix that will be prepended to all uploads
AWS_LOCATION = 'static'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

# File storage
PUBLIC_MEDIA_LOCATION = 'media'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
MEDIA_ROOT = MEDIA_URL
DEFAULT_FILE_STORAGE = 'rfis.storage_backends.PrivateFileStorage'