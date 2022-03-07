from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if bool(int(os.getenv("DEBUG", "0"))):
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
    MEDIA_URL = 'media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
else: # import aws settings
    from .aws import *

# Django Static Files Directory
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)