from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if not os.getenv("DEBUG"): # if DEBUG environment variable is set dont load the .env file
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env.dev"))

if bool(int(os.getenv("DEBUG", "0"))):
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
    MEDIA_URL = 'media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
else:
    # Boto3
    #DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'rfis.storage_backends.S3StaticStorage'
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

# Django Static Files Directory
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)