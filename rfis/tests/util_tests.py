from django.contrib.auth import get_user_model
from django.test import TestCase

from .. import constants as c
from .. import email_parser as eparser
from .. import models as m
from .. import utils as u
from . import gmail_mock
from . import utils as tu


def add_from_users_threads():
    parser = eparser.GmailParser()
    gmail_service = gmail_mock.GmailServiceMock()
    gmail_threads = gmail_service.get_threads()
    for gmail_thread_id in gmail_threads:
        single_gmail_thread = gmail_service.get_thread(gmail_thread_id["id"])
        for msg in single_gmail_thread.get("messages"):
            # Only create users that initiated the thread.
            # When the message id and thread id are the same
            # its the first message in the thread
            if msg["id"] == msg["threadId"]:
                parser.parse(msg)
                get_user_model().objects.get_or_create(email=parser.fromm)


class UtilsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_from_users_threads()
        tu.create_default_db_entries()
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

    def test_should_create_thread(self):
        thread = m.Thread.objects.all().first()
        self.assertEqual(u.should_create_thread(thread.gmail_thread_id, ""), True)
        self.assertEqual(
            u.should_create_thread(
                thread.gmail_thread_id, thread.message_thread_initiator.email
            ),
            True,
        )
        self.assertEqual(
            u.should_create_thread("", thread.message_thread_initiator.email), True
        )
        self.assertEqual(u.should_create_thread("", ""), False)

    def test_create_db_entry_from_parser(self):
        parser = eparser.GmailParser()
        gmail_messages = self.gmail_service.get_messages()
        for gmail_message_id in gmail_messages["messages"]:
            single_gmail_message = self.gmail_service.get_message(gmail_message_id["id"])
            # Create all of the messages that started the threads
            if single_gmail_message["id"] == single_gmail_message["threadId"]:
                created = u.create_db_entry_from_parser(parser, single_gmail_message)
                thread = m.Thread.objects.get(gmail_thread_id=parser.thread_id)
                message = m.Message.objects.get(message_id=parser.message_id)
                attachments_count = m.Attachment.objects.filter(
                    message_id=message
                ).count()
                self.assertEqual(attachments_count, len(parser.files_info))
        # After creating all of the first messages in a thread now check that
        # the rest of the messages in the thread will be added successfully
        for gmail_message_id in gmail_messages["messages"]:
            single_gmail_message = self.gmail_service.get_message(gmail_message_id["id"])
            created = u.create_db_entry_from_parser(parser, single_gmail_message)
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
                single_gmail_thread["messages"], parser
            )
            thread = m.Thread.objects.get(gmail_thread_id=parser.thread_id)
            message = m.Message.objects.get(message_id=parser.message_id)
            attachments_count = m.Attachment.objects.filter(message_id=message).count()
            self.assertEqual(attachments_count, len(parser.files_info))

    def test_process_multiple_gmail_threads(self):
        parser = eparser.GmailParser()
        read_messages = u.process_multiple_gmail_threads(self.gmail_service, parser)
        self.assertEqual(type(read_messages), list)
