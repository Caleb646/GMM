from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ... import models as m
from .. import utils as tu


class MessageManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = tu.create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_message_log(self):
        dashboards = m.MessageLog.objects.all()
        for dash in dashboards:
            url = reverse("message_log_detailed", args=[dash.slug])
            threads = m.Thread.objects.filter(message_thread_initiator=dash.owner)
            # TODO test formset
            # unauthenticated user should get redirected
            tu.redirect_auth_check(url, "", 302, tu.redirect_join(tu.USER_LOGIN, url))

            # user who is not a super user or staff or owner of the dashboard
            # should get denied
            user = get_user_model().objects.all().exclude(email=dash.owner.email).first()
            tu.auth_check(url, user.email, 403)

            tu.auth_check(url, "staff", 200)
            tu.auth_check(url, "admin", 200)
            # owner of the dashboard should be able to see it
            tu.auth_check(url, dash.owner.email, 200)
