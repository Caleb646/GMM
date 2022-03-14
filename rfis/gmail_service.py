import json
from functools import wraps
from typing import List

from constance import config
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from . import constants as c
from . import models as m
from . import utils as u


def token_refresh(method):
    @wraps(method)
    def refresh(self: "GmailService", *args, **kwargs):
        # check if token is valid before making a request
        # if not try to refresh it
        if (
            not self.token
            or not self.token.valid
            or self.token.expired
            and self.token.refresh_token
        ):
            self._refresh_token()
        return method(self, *args, **kwargs)

    return refresh


class GmailService:
    def __init__(self) -> None:
        self.token: Credentials = None
        self.service = self._build_service()

    @staticmethod
    def load_client_secret_file():
        return u.load_file(config.GMAIL_WEB_CLIENT_SECRET, json.load)

    @staticmethod
    def load_client_token():
        credentials = m.GmailCredentials.load()
        assert credentials, "Credentials cannot be None"
        return credentials.credentials

    @staticmethod
    def save_client_token(credentials: Credentials):
        db_credentials = m.GmailCredentials.load()
        db_credentials.credentials = credentials.to_json()
        db_credentials.save()

    def get_credentials(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        creds = Credentials.from_authorized_user_info(
            GmailService.load_client_token(), c.GMAIL_API_SCOPES
        )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise ValueError("Credentials cannot be null or expired")
        self.token = creds
        GmailService.save_client_token(self.token)  # write token to file for later use

    def _refresh_token(self):
        self.token.refresh(Request())
        GmailService.save_client_token(self.token)

    def _build_service(self):
        self.get_credentials()
        return build("gmail", "v1", credentials=self.token)

    @token_refresh
    def get_threads(self, query_params="label:inbox is:unread"):
        return (
            self.service.users()
            .threads()
            .list(userId="me", q=query_params)
            .execute()
            .get("threads", [])
        )

    @token_refresh
    def get_thread(self, thread_id):
        return (
            self.service.users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )

    @token_refresh
    def get_messages(self, query_params="label:inbox is:unread"):
        return self.service.users().messages().list(userId="me", q=query_params).execute()

    @token_refresh
    def get_message(self, message_id):
        return (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

    @token_refresh
    def mark_read_messages(self, read_messages: List[int]):
        if not read_messages:
            return
        body = {"ids": read_messages, "addLabelIds": [], "removeLabelIds": ["UNREAD"]}
        self.service.users().messages().batchModify(userId="me", body=body).execute()

    @token_refresh
    def get_attachment(self, message_id, attachment_id):
        return (
            self.service.users()
            .messages()
            .attachments()
            .get(userId="me", id=attachment_id, messageId=message_id)
            .execute()
        )
