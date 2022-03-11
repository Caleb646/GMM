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


class EmailParserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = gmail_mock.GmailServiceMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    # def test_email_parser(self):
    #     for msg in data["test_messages"]:
    #         self._parser.parse(msg["raw_gmail_message"])

    #         answer = msg["parsed_message"]
    #         tested = self._parser.format_test_data()

    #         # Because part of the email address parsing uses a
    #         # set to remove duplicates the order is sometimes not the same.
    #         # This fixes that and makes them comparable.
    #         answer["To"] = sorted(answer["To"])
    #         tested["To"] = sorted(tested["To"])

    #         self.assertDictEqual(tested, answer)  # ,f"\n\nTest: {tested}\n\nAnswer: {answer}")
