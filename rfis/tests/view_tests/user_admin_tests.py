from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ... import constants as c
from ... import models as m
from .. import utils as testu
from .. import utils as tu


class MessageManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = tu.create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_thread_detailed(self):
        threads = m.Thread.objects.all()

        for t in threads:
            url = reverse("user:message_thread_detailed_view", args=[t.id])
            testu.redirect_auth_check(
                url, "", 302, testu.redirect_join(testu.USER_ADMIN_LOGIN, url)
            )
            testu.auth_check(url, "test1", 200, False)
            testu.auth_check(url, "staff", 200, False)
            response = testu.auth_check(url, "admin", 200, False)
            r_messages = testu.from_context(response.context, "my_messages")
            r_attachments = testu.from_context(response.context, "my_attachments")
            messages = m.Message.objects.filter(message_thread_id=t)

            # ensure that there are not duplicates
            attachments = (
                m.Attachment.objects.filter(message_id__in=[m.id for m in messages])
                .order_by("gmail_attachment_id")
                .distinct("gmail_attachment_id")
            )
            # assert that
            # 1. messages are in the appropriate order
            # 2. there are no duplicate messages
            self.assertListEqual(
                [m.message_id for m in messages],
                [msg.message_id for msg in r_messages],
            )

            # assert that
            # 1. attachments are in the appropriate order
            # 2. there are no duplicate attachments
            self.assertListEqual(
                [atx.gmail_attachment_id for atx in attachments],
                [a.gmail_attachment_id for a in r_attachments],
            )
