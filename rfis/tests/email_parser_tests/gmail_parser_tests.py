import json
import os

from django.conf import settings
from django.test import TestCase

from ... import constants as c
from ... import email_parser as eparser
from ... import models as m
from .. import gmail_mock


class EmailParserTestCase(TestCase):
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
