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
        for thread in threads:
            url = reverse("user:message_thread_detailed_view", args=[thread.id])

            # unauthenticated user should get redirected
            testu.redirect_auth_check(
                url, "", 302, testu.redirect_join(testu.USER_ADMIN_LOGIN, url)
            )
            testu.auth_check(url, "", 302)
            testu.auth_check(url, "test1", 200)
            testu.auth_check(url, "staff", 200)
            response = testu.auth_check(url, "admin", 200)
            # https://docs.djangoproject.com/en/4.0/topics/testing/tools/
            # context is a list of contexts
            messages = m.Message.objects.filter(message_thread_id=thread)
            view_messages = testu.from_context(response.context, "my_messages")
            difference = messages.difference(view_messages)
            self.assertEqual(
                difference.count(), 0, f"\n\ndifference: {difference.values_list()}"
            )

            attachments = m.Attachment.objects.filter(
                message_id__in=[m.id for m in messages]
            )
            view_attachments = testu.from_context(response.context, "my_attachments")
            difference = attachments.difference(view_attachments)
            self.assertEqual(
                difference.count(), 0, f"\n\ndifference: {difference.values_list()}"
            )
