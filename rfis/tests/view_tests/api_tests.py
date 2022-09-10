from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ... import models as m
from .. import utils as testu


class ApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = testu.create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_get_messages_for_thread(self):
        threads = m.Thread.objects.all()
        for thread in threads:
            dashboard = m.MessageLog.objects.get(owner=thread.message_thread_initiator)
            url = reverse("api_get_all_thread_messages", args=[thread.gmail_thread_id])
            # unauthenticated user should get redirected
            testu.redirect_auth_check(
                url, "", 302, testu.redirect_join(testu.USER_LOGIN, url)
            )
            testu.auth_check(url, "staff", 200)
            testu.auth_check(url, "admin", 200)
            # owner of the dashboard should be able to see it
            response = testu.auth_check(url, dashboard.owner.email, 200)
            messages = m.Message.objects.filter(message_thread_id=thread).values("pk")
            self.assertListEqual(
                [msg["pk"] for msg in messages],
                testu.json_to_list(response.json()["data"]["messages"], "pk"),
            )

    def test_get_unread_messages(self):
        url = reverse("gmail_get_unread_messages")
        testu.basic_auth_check(url, "", 401)
        # user = get_user_model().objects.first()
        # TODO cannot test a successful auth of this view because of how
        # gmail access/refresh tokens are saved
        # basic_auth_check(url, user.email, 200)

    def test_notify_users_of_open_messages(self):
        # TODO test that only threads with users that have the can_notify set to True and
        # threads that are OPEN
        url = reverse("notify_users_of_open_messages")
        testu.basic_auth_check(url, "", 401)
        user = get_user_model().objects.first()
        testu.basic_auth_check(url, user.email, 200)
