import math
import os
import json
from time import sleep
from dateparser import parse
from functools import wraps
from typing import Dict, List

from django.conf import settings

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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
    #TODO move into a thread parser
    def find_earliest_message_index(self, messages: List[Dict]):
        earliest_message_index = 0
        earliest_message_time = math.inf
        for i, msg in enumerate(messages):
            msg_date = int(msg["internalDate"])
            if msg_date < earliest_message_time:
                earliest_message_time = msg_date 
                earliest_message_index = i
        return earliest_message_index

    @token_refresh
    def get_threads(self, query_params = "label:inbox is:unread", *args, **kwargs):
        return self.service.users().threads().list(userId='me', q=query_params).execute().get('threads', [])
    
    @token_refresh
    def get_thread(self, thread_id, *args, **kwargs):
        return self.service.users().threads().get(userId='me', id=thread_id, format='full').execute()

    @token_refresh
    def get_unread_messages(self, *args, **kwargs):
        return self.service.users().messages().list(userId='me', q="label:inbox is:unread").execute()

    @token_refresh
    def get_message(self, message_id, *args, **kwargs):
        return self.service.users().messages().get(userId='me', id=message_id, format='full').execute()

    @token_refresh
    def mark_read_messages(self):
        if len(self.messages_read) == 0:
            return
        body = {'ids' : self.messages_read, 'addLabelIds': [], 'removeLabelIds': ['UNREAD']}
        self.service.users().messages().batchModify(userId='me', body=body).execute()


def get_test_message(message_id):
    service = GmailService()
    parser = GmailParser()
    raw_message = service.get_message(message_id)
    parser.parse(raw_message)
    #print("\n\nraw message: ", raw_message, "\n\n")
    #print("\n\nchosen: ", parser.body, "\n\n")

def get_test_thread(thread_id):
    service = GmailService()
    # parser = GmailParser()
    # parser.parse(service.get_message(message_id))
    # print(parser._chosen)
    # print(f"thread_type: {parser.thread_type}")
    thread = service.get_thread(thread_id)
    print(f"\n\nGmail Internal Date: {parse(thread['messages'][0]['internalDate'])}")
    print(thread)
    #print(service.get_threads())