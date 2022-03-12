import base64
import json
import os
import random
import uuid
from http.cookies import SimpleCookie
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.template.loader import render_to_string
from django.test import Client, TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from google.oauth2.credentials import Credentials

from .. import constants as c
from .. import email_parser as eparser
from .. import gmail_service
from .. import models as m
from .. import utils as u
from . import gmail_mock


class UtilsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gmail_service = gmail_mock.GmailServiceMock()
        cls.default_data = {
            "jobs": {
                c.FIELD_VALUE_UNKNOWN_JOB: m.Job.objects.get_or_create(
                    name=c.FIELD_VALUE_UNKNOWN_JOB
                ),
                "Test Job": m.Job.objects.get_or_create(name="Test Job"),
            },
            "thread_types": {
                "1": m.ThreadType.objects.get_or_create(
                    name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE
                ),
                "2": m.ThreadType.objects.get_or_create(name="RFI"),
            },
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_create_db_entry_from_parser(self):
        parser = eparser.GmailParser()
        gmail_messages = self.gmail_service.get_messages()
        for gmail_message_id in gmail_messages["messages"]:
            single_gmail_message = self.gmail_service.get_message(gmail_message_id["id"])
            created = u.create_db_entry_from_parser(
                parser, single_gmail_message, create_from_any_user=True
            )
            thread = m.Thread.objects.get(gmail_thread_id=parser.thread_id)
            message = m.Message.objects.get(message_id=parser.message_id)
            attachments_count = m.Attachment.objects.filter(message_id=message).count()
            self.assertEqual(attachments_count, len(parser.files_info))

    def test_find_earliest_message_index(self):
        gmail_threads = self.gmail_service.get_threads()
        for id in gmail_threads:
            thread = self.gmail_service.get_thread(id["id"])
            earliest_message = u.find_earliest_message_index(thread["messages"])
            sorted_msgs = sorted(thread["messages"], key=lambda m: int(m["internalDate"]))
            self.assertEqual(sorted_msgs[0], thread["messages"][earliest_message])

    def test_process_single_gmail_thread(self):
        parser = eparser.GmailParser()
        gmail_threads = self.gmail_service.get_threads()
        for gmail_thread_id in gmail_threads:
            single_gmail_thread = self.gmail_service.get_thread(gmail_thread_id["id"])
            read_messages = u.process_single_gmail_thread(
                single_gmail_thread["messages"], parser, create_from_any_user=True
            )
            thread = m.Thread.objects.get(gmail_thread_id=parser.thread_id)
            message = m.Message.objects.get(message_id=parser.message_id)
            attachments_count = m.Attachment.objects.filter(message_id=message).count()
            self.assertEqual(attachments_count, len(parser.files_info))

    def test_process_multiple_gmail_threads(self):
        parser = eparser.GmailParser()
        read_messages = u.process_multiple_gmail_threads(
            self.gmail_service, parser, create_from_any_user=True
        )
        self.assertEqual(type(read_messages), list)
