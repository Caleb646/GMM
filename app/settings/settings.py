from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if not os.getenv("DEBUG"): # if DEBUG environment variable is set dont load the .env file
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env.dev"))

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = bool(int(os.getenv("DEBUG", default="0")))
ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")
DOMAIN_URL = os.environ["DOMAIN_URL"]

# the cron user should be a normal user not a superuser
CRON_USER_NAME = os.environ["CRON_USER_NAME"] 
CRON_USER_PASSWORD = os.environ["CRON_USER_PASSWORD"]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', 

    # third party apps
    "admin_searchable_dropdown",
    "storages",
    "constance",
    "constance.backends.database",
    #'django_crontab',

    # my apps
    'rfis', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'rfis.context_processors.get_domain_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

if os.getenv("DATABASE_URL"):
    DATABASES = {
        'default': dj_database_url.config(env='DATABASE_URL', conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE':os.environ["SQL_ENGINE"],
            'NAME': os.environ["SQL_DATABASE"],
            'USER': os.environ["POSTGRES_USER"],
            'PASSWORD': os.environ["POSTGRES_PASSWORD"],
            'HOST': os.environ["SQL_HOST"],
            'PORT': os.environ["SQL_PORT"]
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


####################### Django-Cron Setup ###############################################

# use python manage.py crontab add to update CRONJOBS
# use python manage.py crontab show to show active CRONJOBS
# use python manage.py crontab remove to remove all active CRONJOBS
# CRONJOBS = [
#     ('0 0 1 * *', 'myapp.cron.other_cron_job', ['pos_arg1', 'pos_arg2'], {'verbose': 'key_arg'}),
# ]

########################################################################################



####################### My Auth Settings ###############################################
AUTH_USER_MODEL = 'rfis.MyUser'
########################################################################################



####################### Email Setup ###############################################
# needed for initial setup
ADMINS_INFO = [(ainfo.split(",")[0], ainfo.split(",")[1], ainfo.split(",")[2]) for ainfo in os.environ["ADMINS"].split("|") if ainfo != ""]
# needed for the AdminEmailHandler to work
ADMINS =  [(name, email) for name, email, password in ADMINS_INFO]
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USERNAME']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
########################################################################################



LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'EST'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


USE_SSL = bool(int(os.getenv("USE_SSL", default="1"))) # default to true

# CORS_REPLACE_HTTPS_REFERER      = not DEBUG
# HOST_SCHEME                     = "https://" if not DEBUG else "http://"
# SECURE_PROXY_SSL_HEADER         = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else ()
SECURE_SSL_REDIRECT             = USE_SSL
SESSION_COOKIE_SECURE           = USE_SSL
CSRF_COOKIE_SECURE              = USE_SSL
# SECURE_HSTS_INCLUDE_SUBDOMAINS  = not DEBUG
# SECURE_HSTS_SECONDS             = 1000000
# SECURE_FRAME_DENY               = not DEBUG