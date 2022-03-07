import math
import os
import json
from dateparser import parse
from functools import wraps
from typing import Dict, List

from django.core.files.storage import default_storage
from django.core.files import base

from constance import config
from storages.backends.s3boto3 import S3Boto3Storage, S3Boto3StorageFile

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from . import constants as c, email_parser

def token_refresh(method):
    @wraps(method)
    def refresh(self: "GmailService", *args, **kwargs):
        # check if token is valid before making a request
        # if not try to refresh it
        if not self.token or not self.token.valid or self.token.expired and self.token.refresh_token:
            self._refresh_token()
        return method(self, *args, **kwargs)
    return refresh


class GmailService():
    def __init__(self) -> None:
        self.token: Credentials = None
        self.service = self._build_service()
        self.messages_read: List[Dict[str : str]] = []

    @staticmethod
    def load_client_secret_config_f_file():
        head, tail = os.path.split(config.GMAIL_WEB_CLIENT_SECRET)
        assert default_storage.exists(name=tail)
        if isinstance(default_storage, S3Boto3Storage):
            file: S3Boto3StorageFile = default_storage.open(tail, "rb")
            data = json.load(file)
            file.close()
            return data
        return json.load(default_storage.open(tail, "rb"))

    @staticmethod
    def load_client_token():
        #storage_class = get_storage_class()()
        assert default_storage.exists(name=c.GMAIL_API_CREDENTIALS_FILENAME)
        if isinstance(default_storage, S3Boto3Storage):
            file: S3Boto3StorageFile = default_storage.open(c.GMAIL_API_CREDENTIALS_FILENAME, "rb")
            data = json.load(file)
            file.close()
            return data
        return json.load(default_storage.open(c.GMAIL_API_CREDENTIALS_FILENAME, "rb"))

    @staticmethod
    def save_client_token(credentials: Credentials):
        if isinstance(default_storage, S3Boto3Storage):
            file: S3Boto3StorageFile = default_storage.open(c.GMAIL_API_CREDENTIALS_FILENAME, "w")
            file.write(credentials.to_json())
            file.close()
        else:
            if default_storage.exists(name=c.GMAIL_API_CREDENTIALS_FILENAME):
                default_storage.delete(c.GMAIL_API_CREDENTIALS_FILENAME)
            default_storage.save(c.GMAIL_API_CREDENTIALS_FILENAME, 
                base.ContentFile(credentials.to_json(), c.GMAIL_API_CREDENTIALS_FILENAME)
            )

    def get_credentials(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        loaded_creds = GmailService.load_client_token()
        creds = Credentials.from_authorized_user_info(GmailService.load_client_token(), c.GMAIL_API_SCOPES)
            #creds = Credentials.from_authorized_user_file(c.GMAIL_API_CREDENTIALS_FILENAME, c.GMAIL_API_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise ValueError("Credentials cannot be null or expired")
        self.token = creds
        GmailService.save_client_token(self.token) # write token to file for later use

    def _refresh_token(self):
        self.token.refresh(Request())
        GmailService.save_client_token(self.token)

    def _build_service(self, *args, **kwargs):
        self.get_credentials()
        return build('gmail', 'v1', credentials=self.token)

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

    @token_refresh
    def get_attachment(self, message_id, attachment_id, *args, **kwargs):
        return self.service.users().messages().attachments().get(userId='me', id=attachment_id, messageId=message_id).execute()


def get_test_message(message_id):
    service = GmailService()
    parser = email_parser.GmailParser()
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