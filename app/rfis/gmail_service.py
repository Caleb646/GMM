import os.path
from base64 import urlsafe_b64decode
from datetime import datetime
from typing import Dict, List

from django.conf import settings

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Job, MessageThread, Message, Attachment

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']


class GmailService():
    def __init__(self) -> None:
        self.service = self.build_service()
        self.messages_read = []

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

        return creds

    #TODO need a way to refresh token on fail
    #use a decorator
    def build_service(self):
        return build('gmail', 'v1', credentials=self.get_credentials())

    def get_threads(self):
        return self.service.users().threads().list(userId='me', q="label:inbox").execute().get('threads', [])

    def get_unread_messages(self):
        try:
            return self.service.users().messages().list(userId='me', q="label:inbox is:unread").execute()
        except:
            return None

    def get_message(self, message_id):
        try:
            return self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
        except:
            return None
    #TODO implement
    def mark_read_messages(self):
        pass
    
    def parse_parts(self, parts, msg):
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
                msg += urlsafe_b64decode(data).decode()
                print("Message: ", msg)

            elif mimeType == "text/html":
                print("Not doing anything with html yet.")

        return msg

    def parse_headers(self, headers):
        data = {}
        for h in headers:
            if h["name"] == "Subject":
                data["Subject"] = h["value"]
            elif h["name"] == "From":
                data["From"] = h["value"]
            elif h["name"] == "To":
                data["To"] = h["value"]
            elif h["name"] == "Date":
                data["Date"] = h["value"]
        return data

    def parse_subject(self, subject: str):
        data = {}
        parts = subject.split(" ")
        data["ThreadType"] = parts[0]
        data["JobName"] = parts[1]
        return data

def parse_email(email: str):
    """
    Emails from Gmail will sometimes be in the form
    Name <email> or name email this function pulls the email out.
    """
    index = email.find("@")
    if index == -1:
        print("Malformed Email")
        return "Malformed Email"
    right = index
    while right < len(email) and email[right] not in (">", "<", " ", "/"):
        right += 1
    left = index
    while left >= 0 and email[left] not in (">", "<", " ", "/"):
        left -= 1
    return email[left + 1 : right]



def add_unread_messages():
    service = GmailService()
    unread_message_ids: List[Dict] = service.get_unread_messages()

    for m_id in unread_message_ids["messages"]:
        service.messages_read.append(m_id)
        message = service.get_message(m_id["id"])
        if message:
            txt = service.parse_parts(message["payload"]["parts"], "")
            headers = service.parse_headers(message["payload"]["headers"])
            threadtype_jobname = service.parse_subject(headers["Subject"])

            #TODO fix date time

            job = Job.objects.get_or_unknown(threadtype_jobname["JobName"])
            message_thread = MessageThread.objects.create_or_get(
                m_id["threadId"], job_id=job,
                due_date=datetime.utcnow(),
                message_thread_initiator=parse_email(headers["From"])
            )
            my_message = Message.objects.create_or_get(
                m_id["id"],
                message_thread_id=message_thread,
                subject=headers["Subject"],
                body=txt,
                fromm=parse_email(headers["From"]),
                to=headers["To"],
                #time_received=datetime.strptime(headers["Date"], "%a %d %b %Y %X %z")
                time_received=datetime.utcnow()
            )
    service.mark_read_messages()