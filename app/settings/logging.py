import os
import logging
from logdna import LogDNAHandler #  required to register `logging.handlers.LogDNAHandler`

if log_dna_key := os.environ.get("LOGDNA_KEY"):
    logdna_handler = {
            'level': logging.DEBUG,
            'class': 'logging.handlers.LogDNAHandler',
            'key': log_dna_key,
        },

else:
    logdna_handler = {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {name} {module} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "verbose",
            "include_html": True,
        },
        "logdna" : logdna_handler
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["logdna"],
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security.*": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends.schema": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
