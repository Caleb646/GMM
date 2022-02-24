import os.path
from base64 import urlsafe_b64decode
from datetime import datetime
from time import sleep
from dateparser import parse
from functools import wraps
from typing import Dict, List
from email import parser, message as py_email_message, policy
import re

from django.conf import settings

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Job, MessageThread, Message, Attachment
from .email_parser import EmailReplyParser

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']


def token_refresh(method):
    @wraps(method)
    def refresh(self: "GmailService", *args, **kwargs):
        if not self.token or not self.token.valid:
            if self.token and self.token.expired and self.token.refresh_token:
                try:
                    self.token.refresh(Request())
                except Exception as e:
                    print(f"Failed to refresh token: {method.__func__} {e}")
            else:
                print("Cannot renew token without a refresh token")
        return method(self, *args, **kwargs)
    return refresh

#TODO need a logger that will email me
def error_handler(method):
    @wraps(method)
    def handler(self: "GmailService", *args, **kwargs):
        try:
            return method(self, args, kwargs)
        except Exception as e:
            print(f"Method encountered a fatal error: {e}")
            return None
    return handler

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
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(settings.GMAIL_SECRETS, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        self.token = creds
        return creds

    #TODO need a way to refresh token on fail
    #use a decorator
    #@error_handler
    def build_service(self, *args, **kwargs):
        return build('gmail', 'v1', credentials=self.get_credentials())

    #@error_handler
    @token_refresh
    def get_threads(self, *args, **kwargs):
        return self.service.users().threads().list(userId='me', q="label:inbox").execute().get('threads', [])

    #@error_handler
    @token_refresh
    def get_unread_messages(self, *args, **kwargs):
        try:
            return self.service.users().messages().list(userId='me', q="label:inbox is:unread").execute()
        except:
            return None

    #@error_handler
    @token_refresh
    def get_message(self, message_id, *args, **kwargs):
        try:
            return self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
        except:
            return None

    #@error_handler
    @token_refresh
    def mark_read_messages(self):
        body = {'ids' : [msg["id"] for msg in self.messages_read], 'addLabelIds': [], 'removeLabelIds': ['UNREAD']}
        self.service.users().messages().batchModify(userId='me', body=body).execute()
    
    #@error_handler
    def parse_parts(self, parts, msg, *args, **kwargs):     
        if not parts:
            return msg

        for p in parts:
            filename = p.get("filename")
            mimeType = p.get("mimeType")
            body = p.get("body")
            data = body.get("data")
            file_size = body.get("size")
            p_headers = p.get("headers")
            if p.get("parts"):
                self.parse_parts(p.get("parts"), msg)
            if mimeType == "text/plain" and data:
                msg = parser.BytesParser(_class=py_email_message.EmailMessage, policy=policy.default).parsebytes(urlsafe_b64decode(data))
        return msg

    #@error_handler
    def parse_headers(self, headers, *args, **kwargs):
        data = {
            "Subject": "Unknown",
            "From": "Unknown",
            "To": "Unknown",
            "Date": f"{datetime.utcnow()}"
        }
        for h in headers:
            head = h.get("name")
            value = h.get("value")
            if head == "Subject":
                data["Subject"] = value
            elif head == "From":
                data["From"] = value
            elif head == "To":
                data["To"] = value
            elif head == "Date":
                data["Date"] = value
        return data

    #@error_handler
    def parse_subject(self, subject: str, *args, **kwargs):
        data = {
            "ThreadType" : settings.DEFAULT_THREAD_TYPE,
            "JobName" : settings.DEFAULT_JOB_NAME
        }
        if subject is None or subject == "":
            return data
        pattern = r'(RE:|RE|Re:|FW|FW:|Fw:)'
        fields = ["ThreadType", "JobName"]
        parts = subject.split(" ")
        for i in range(min(len(fields), len(parts))):
            data[fields[i]] = parts[i]
        return data

def parse_email_address(email: str):
    """
    Emails from Gmail will sometimes be in the form
    Name <email> or name email this function pulls the email out.
    """
    index = email.find("@")
    if index == -1:
        return "Unknown"
    right = index
    while right < len(email) and email[right] not in (">", "<", " ", "/"):
        right += 1
    left = index
    while left >= 0 and email[left] not in (">", "<", " ", "/"):
        left -= 1
    return email[left + 1 : right]

#TODO cleanup parsing, middle reply was lost for some reason out of the three replies, dont parse emails,
def add_unread_messages():
    service = GmailService()
    unread_message_ids: List[Dict] = service.get_unread_messages().get("messages")
    if unread_message_ids is None:
        return
    current_count = 0
    max_count_before_sleep = 25
    for m_id in unread_message_ids:
        current_count += 1
        #rate limit requests
        if current_count > max_count_before_sleep:
            current_count = 0
            sleep(0.25)
        #store message id and thread id so these messages can be marked
        #as read later
        service.messages_read.append(m_id)
        message = service.get_message(m_id["id"])
        payload = message.get("payload")
        if message and payload:
            txt = service.parse_parts(payload.get("parts"), py_email_message.EmailMessage())
            headers = service.parse_headers(payload.get("headers"))
            threadtype_jobname = service.parse_subject(headers.get("Subject"))

            print("\n\ntxt: ", EmailReplyParser.parse_reply(str(txt.get_body())))
            # print("Headers: ", headers)
            # print("threadtype_jobname", threadtype_jobname)
            # print("\n\n")
            job = Job.objects.get_or_unknown(threadtype_jobname["JobName"])
            message_thread = MessageThread.objects.create_or_get(
                m_id["threadId"], job_id=job,
                subject=headers["Subject"],
                due_date=datetime.utcnow(),
                message_thread_initiator=headers["From"]
            )
            my_message = Message.objects.create_or_get(
                m_id["id"],
                message_thread_id=message_thread,
                subject=headers["Subject"],
                body=txt,
                fromm=headers["From"],
                to=headers["To"],
                #time_received=datetime.strptime(headers["Date"], "%a %d %b %Y %X %z")
                time_received=parse(headers["Date"])
            )
    #service.mark_read_messages()