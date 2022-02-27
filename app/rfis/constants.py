from django.conf import settings
import os

GMAIL_CLIENT_SECRET_FILENAME = "gmail_web_client_secret.json"
GMAIL_API_CREDENTIALS_FILENAME = "gmail_web_credentials.json"
GMAIL_REDIRECT_URI = settings.DOMAIN_URL + "/gmail-api/gmail-oauth-callback/"
GMAIL_API_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
GMAIL_API_SESSION_STATE_FIELDNAME = "state"

EMAIL_TEST_DATA_PATH = os.path.join(settings.BASE_DIR, "gmail_test_data.json")