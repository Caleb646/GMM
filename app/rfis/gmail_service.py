from multiprocessing.sharedctypes import Value
import os.path
from time import sleep
from dateparser import parse
from functools import wraps
from typing import Dict, List

from django.conf import settings

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Job, MessageThread, Message, Attachment
from .email_parser import GmailParser
from . import constants as c

def token_refresh(method):
    @wraps(method)
    def refresh(self: "GmailService", *args, **kwargs):
        # check if token is valid before making a request
        # if not try to refresh it
        if not self.token or not self.token.valid or self.token.expired and self.token.refresh_token:
            self._refresh_token()
        return method(self, *args, **kwargs)
    return refresh


#TODO need to deal with spam mail somehow. Maybe only accept messages from pre-approved users
class GmailService():
    def __init__(self) -> None:
        self.token: Credentials = None
        self.service = self.build_service()
        self.messages_read: List[Dict[str : str]] = []

    def get_credentials(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(c.GMAIL_API_CREDENTIALS_FILENAME):
            creds = Credentials.from_authorized_user_file(c.GMAIL_API_CREDENTIALS_FILENAME, c.GMAIL_API_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise ValueError("Credentials cannot be null or expired")
        self.token = creds
        self._save_token() # write token to file for later use
        return creds

    def _refresh_token(self):
        self.token.refresh(Request())
        self._save_token()
    
    def _save_token(self):
        with open(c.GMAIL_API_CREDENTIALS_FILENAME, 'w') as f:
            f.write(self.token.to_json())

    def build_service(self, *args, **kwargs):
        return build('gmail', 'v1', credentials=self.get_credentials())

    @token_refresh
    def get_threads(self, *args, **kwargs):
        return self.service.users().threads().list(userId='me', q="label:inbox").execute().get('threads', [])

    @token_refresh
    def get_unread_messages(self, *args, **kwargs):
        return self.service.users().messages().list(userId='me', q="label:inbox is:unread").execute()

    @token_refresh
    def get_message(self, message_id, *args, **kwargs):
        return self.service.users().messages().get(userId='me', id=message_id, format='full').execute()

    @token_refresh
    def mark_read_messages(self):
        body = {'ids' : [msg["id"] for msg in self.messages_read], 'addLabelIds': [], 'removeLabelIds': ['UNREAD']}
        self.service.users().messages().batchModify(userId='me', body=body).execute()

def add_unread_messages():
    service = GmailService()
    g_parser = GmailParser()
    unread_message_ids: List[Dict] = service.get_unread_messages().get("messages")
    if not unread_message_ids:
        return
    current_count = 0
    max_count_before_sleep = 25
    for m_id in unread_message_ids:
        current_count += 1
        #rate limit requests
        if current_count > max_count_before_sleep:
            current_count = 0
            sleep(0.25)
        #store message id so these messages can be marked as read later
        service.messages_read.append(m_id)
        g_parser.parse(service.get_message(m_id["id"]))

        job = Job.objects.get_or_unknown(g_parser.job_name)
        message_thread = MessageThread.objects.create_or_get(
            g_parser.thread_id,
            job_id=job,
            subject=g_parser.subject,
            message_thread_initiator=g_parser.fromm
        )
        Message.objects.create_or_get(
            g_parser.message_id,
            message_thread_id=message_thread,
            subject=g_parser.subject,
            body=g_parser.body,
            debug_unparsed_body=g_parser.debug_unparsed_body,
            fromm=g_parser.fromm,
            to=g_parser.to,
            #time_received=datetime.strptime(headers["Date"], "%a %d %b %Y %X %z")
            time_received=parse(g_parser.date)
        )
    #TODO uncomment
    #service.mark_read_messages()

def get_test_message(message_id):
    service = GmailService()
    parser = GmailParser()
    parser.parse(service.get_message(message_id))
    print(parser._chosen)