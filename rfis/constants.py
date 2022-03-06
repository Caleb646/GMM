from django.conf import settings
import os

GMAIL_API_CREDENTIALS_FILENAME = "gmail_web_credentials.json"
GMAIL_REDIRECT_URI = settings.DOMAIN_URL + "/gmail-api/gmail-oauth-callback/"
GMAIL_API_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
GMAIL_API_SESSION_STATE_FIELDNAME = "state"

EMAIL_TEST_DATA_PATH = os.path.join(settings.BASE_DIR, "gmail_test_data.json")


FIELD_VALUE_UNKNOWN_JOB = "Unknown"
FIELD_VALUE_UNKNOWN_THREAD_TYPE = "Unknown"
FIELD_VALUE_RFI_THREAD_TYPE = "RFI"
FIELD_VALUE_CLOSED_THREAD_STATUS = "CLOSED"
FIELD_VALUE_OPEN_THREAD_STATUS = "OPEN"
FIELD_VALUE_ROBOT_USER_TYPE = "ROBOT"
FIELD_VALUE_EMPLOYEE_USER_TYPE = "EMPLOYEE"
FIELD_VALUE_UNKNOWN_USER_TYPE = "Unknown"

JSON_RESPONSE_MSG_KEY = "response_msg"

GROUP_NAME_STAFF_USERS = "Staff"
GROUP_NAME_RECEIVE_NOTIFICATIONS_USERS = "Receive Notifications"