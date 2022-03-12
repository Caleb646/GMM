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
    # TODO need to create test data before refactoring the EmailParser
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.answer_data = json.load(
            open(os.path.join(settings.BASE_DIR, "test_data", "answers.json"), "r")
        )
        cls.service = gmail_mock.GmailServiceMock()
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

    def find_answer(self, message_id, thread_id):
        if ans := list(
            filter(
                lambda ans: ans.get(message_id)
                and ans.get(message_id, {}).get("thread_id") == thread_id,
                self.answer_data["answers"],
            )
        ):
            # remove the gmail id part {"gmail id" : {message test data}}
            return ans[0].pop(message_id)

    def test_email_parser(self):
        parser = eparser.GmailParser()
        threads = self.service.get_threads()
        for tinfo in threads:
            thread = self.service.get_thread(tinfo["id"])
            for msg in thread["messages"]:
                parser.parse(msg)
                answer = self.find_answer(parser.message_id, parser.thread_id)
                test = parser.format_test_data()
                answer["To"] = "".join(sorted(answer["To"]))
                test["To"] = "".join(sorted(test["To"]))
                self.assertDictEqual(test, answer)

                # found = any(
                #     msg.get(parser.message_id) and msg.get(parser.thread_id)
                #     for msg in self.answer_data["answers"]
                # )
                # if found:
                #     continue

                # self.answer_data["answers"].append(
                #     {parser.message_id: parser.format_test_data()}
                # )

        messages = self.service.get_messages()
        for id in messages["messages"]:
            message = self.service.get_message(id["id"])
            parser.parse(message)
            answer = self.find_answer(parser.message_id, parser.thread_id)
            if not answer:
                continue
            test = parser.format_test_data()
            answer["To"] = "".join(sorted(answer["To"]))
            test["To"] = "".join(sorted(test["To"]))
            self.assertDictEqual(test, answer)

        #     found = any(
        #         msg.get(parser.message_id) and msg.get(parser.thread_id)
        #         for msg in self.answer_data["answers"]
        #     )
        #     if found:
        #         continue

        #     self.answer_data["answers"].append(
        #         {parser.message_id: parser.format_test_data()}
        #     )

        # json.dump(
        #     self.answer_data,
        #     open(os.path.join(settings.BASE_DIR, "test_data", "answers.json"), "w"),
        # )
