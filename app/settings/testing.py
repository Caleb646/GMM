import os

from ._constance import *
from .logging import *
from .settings import *
from .storage import *

if not bool(int(os.getenv("TESTING_USE_DEFAULT_STORAGE", "0"))):
    from .aws import *

if bool(int(os.getenv("TESTING_USE_DEFAULT_EMAIL_BACKEND", "0"))):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
