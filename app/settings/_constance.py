from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_ADDITIONAL_FIELDS = {
    'gmail_web_client_secret': ['django.forms.FileField', {}],
    'true_false_field': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((True, "True"), (False, "False"))
    }],
}

CONSTANCE_CONFIG = {
    #'SEND_ALL_USERS_NOTIFICATIONS' : (False, "Or only users with the permission", "true_false_field"),
    #'ACCEPT_ONLY_MESSAGES_FROM_APPROVED_USERS' : (True, "Or all users", "true_false_field"),
    'GMAIL_WEB_CLIENT_SECRET': ("gmail_web_client_secret.json", "Gmail client secret", "gmail_web_client_secret"),
}

CONSTANCE_CONFIG_FIELDSETS = {
    #'User Settings': ('SEND_ALL_USERS_NOTIFICATIONS', 'ACCEPT_ONLY_MESSAGES_FROM_APPROVED_USERS'),
    'Gmail Settings': ('GMAIL_WEB_CLIENT_SECRET',),
}