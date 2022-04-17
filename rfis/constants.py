from django.conf import settings

GMAIL_REDIRECT_URI = settings.DOMAIN_URL + "/gmail-api/gmail-oauth-callback/"
GMAIL_API_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]
GMAIL_API_SESSION_STATE_FIELDNAME = "state"

FIELD_VALUE_UNKNOWN_JOB = "Unknown"
FIELD_VALUE_UNKNOWN_THREAD_TYPE = "Unknown"
FIELD_VALUE_CLOSED_THREAD_STATUS = "CLOSED"
FIELD_VALUE_OPEN_THREAD_STATUS = "OPEN"

JSON_RESPONSE_MSG_KEY = "response_msg"

GROUP_NAME_STAFF_USERS = "Staff"
GROUP_NAME_PROJECT_MANAGER = "Project Manager"
GROUP_NAME_RECEIVE_NOTIFICATIONS_USERS = "Receive Notifications"
