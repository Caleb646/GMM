import logging
import os

from logdna import (
    LogDNAHandler,  # required to register `logging.handlers.LogDNAHandler`
)

if log_dna_key := os.environ.get("LOGDNA_KEY"):
    logdna_handler = {
        "level": logging.INFO,
        "class": "logging.handlers.LogDNAHandler",
        "key": log_dna_key,
        "options": {
            "app": os.environ.get("APP_NAME", "root[logger]"),
        },
    }

else:
    logdna_handler = {  # if logdna key isnt present default to console logging
        "level": logging.INFO,
        # "filters": ["require_debug_true"],
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
        "mail_admins": {
            "level": logging.ERROR,
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "verbose",
            "include_html": True,
        },
        "logdna": logdna_handler,
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["logdna"],
            "level": logging.INFO,
            "propagate": True,
        },
        "django": {
            "level": logging.WARN,
            "handlers": ["logdna"],
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": logging.ERROR,
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["mail_admins"],
            "level": logging.ERROR,
            "propagate": True,
        },
        "django.security.*": {
            "handlers": ["mail_admins"],
            "level": logging.ERROR,
            "propagate": True,
        },
        "django.db.backends.schema": {
            "handlers": ["mail_admins"],
            "level": logging.ERROR,
            "propagate": True,
        },
    },
}
