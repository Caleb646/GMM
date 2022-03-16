import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_ADDITIONAL_FIELDS = {
    "gmail_web_client_secret": ["django.forms.FileField", {}],
    "true_false_field": [
        "django.forms.fields.ChoiceField",
        {"widget": "django.forms.Select", "choices": ((True, "True"), (False, "False"))},
    ],
}

CONSTANCE_CONFIG = {
    #'SEND_ALL_USERS_NOTIFICATIONS' : (False, "Or only users with the permission", "true_false_field"),
    #'ACCEPT_ONLY_MESSAGES_FROM_APPROVED_USERS' : (True, "Or all users", "true_false_field"),
    "GMAIL_WEB_CLIENT_SECRET": (
        "gmail_web_client_secret.json",
        "Gmail client secret",
        "gmail_web_client_secret",
    ),
    "SUBJECT_LINE_PARSER_CONFIDENCE": (
        65,
        "The minimum score required for a message type or job name to be pulled from an"
        " email subject line.",
        int,
    ),
    "DEFAULT_TIMEZONE": ("US/Eastern", "The default timezone.", str),
}

CONSTANCE_CONFIG_FIELDSETS = {
    #'User Settings': ('SEND_ALL_USERS_NOTIFICATIONS', 'ACCEPT_ONLY_MESSAGES_FROM_APPROVED_USERS'),
    "General Settings": ("DEFAULT_TIMEZONE",),
    "Gmail Settings": ("GMAIL_WEB_CLIENT_SECRET",),
    "Email Parser Settings": ("SUBJECT_LINE_PARSER_CONFIDENCE",),
}
