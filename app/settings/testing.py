import os

from .settings import *
from .storage import *
from .constance_settings import *
from .logging import *

if not bool(int(os.getenv("TESTING_USE_DEFAULT_STORAGE", "0"))):
    from .aws import *