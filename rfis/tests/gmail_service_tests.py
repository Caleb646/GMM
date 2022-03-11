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


class GmailServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.gservice = gmail_service.GmailService()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    # @override_settings(DEBUG="0", USE_SSL="0") # set debug to false to use AWS S3 storage
    def test_save_load_tokens_credentials(self):
        client_config = gmail_service.GmailService.load_client_secret_file()
        # test that client id is there
        client_config["web"]["client_id"]

        # test that token and refresh token are present
        token = gmail_service.GmailService.load_client_token()
        token["token"]
        token["refresh_token"]

        # test saving credentials
        creds = Credentials.from_authorized_user_info(
            gmail_service.GmailService.load_client_token(), c.GMAIL_API_SCOPES
        )
        gmail_service.GmailService.save_client_token(creds)

    # will test refresh decorator as well
    # @override_settings(DEBUG="0", USE_SSL="0")
    def test_get_message_thread(self):
        service = gmail_service.GmailService()
        threads = service.get_threads("label:inbox")
        assert len(threads) > 0
        thread = service.get_thread(threads[0]["id"])
        assert thread
        assert thread["messages"]
        message = service.get_message(thread["messages"][0]["id"])
        assert message
