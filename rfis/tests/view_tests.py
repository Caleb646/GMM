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

# import django
# django.setup()


PASSWORD = "1234"
ADMIN_LOGIN = reverse_lazy("admin:login")
USER_LOGIN = reverse_lazy("base_user_login")
client = Client()


def email_password_to_http_auth(email):
    return base64.b64encode(bytes(f"{email}:{PASSWORD}", "utf8")).decode("utf8")


def auth_check(url, email, status_code):
    client.login(email=email, password=PASSWORD)
    response = client.get(url, follow=True)
    client.logout()
    if response.redirect_chain:
        assert any(status_code in route for route in response.redirect_chain), (
            f"Redirect chain {response.redirect_chain} != Target code: {status_code} on"
            f" {url}"
        )
    else:
        assert (
            response.status_code == status_code
        ), f"Response code {response.status_code} != Target code: {status_code} on {url}"
    return response


def basic_auth_check(url, email, status_code):
    client.defaults["HTTP_AUTHORIZATION"] = f"Basic {email_password_to_http_auth(email)}"
    response = client.get(url, follow=True)
    client.defaults["HTTP_AUTHORIZATION"] = SimpleCookie()
    assert (
        response.status_code == status_code
    ), f"Response code {response.status_code} != Target code: {status_code} on {url}"


def redirect_join(to, fromm):
    return urljoin(str(to), f"?next={str(fromm)}")


def redirect_auth_check(url, email, status_code, redirect_url):
    response = auth_check(url, email, status_code)
    found = any(redirect_url in route for route in response.redirect_chain)
    assert (
        found
    ), f"Target Redirect: {redirect_url} not in Redirect Chain: {response.redirect_chain}"


def from_context(context, key):
    if isinstance(context, dict):
        return context.get(key)
    elif not context:
        return None
    for ctx in context:
        if value := from_context(ctx, key):
            return value


def json_to_list(data, key):
    data = json.loads(data)
    return [d[key] for d in data]


def compare_emails(one: mail.EmailMessage, two: mail.EmailMessage):
    assert one.subject == two.subject, f"one: {one.subject} != two: {two.subject}"
    assert one.body == two.body, f"one: {one.body} != two: {two.body}"
    assert one.to == two.to, f"one: {one.to} != two: {two.to}"
    assert (
        one.from_email == two.from_email
    ), f"one: {one.from_email} != two: {two.from_email}"


def return_random_model_instance(model):
    return random.choice(list(model.objects.all()))


def create_dashboards():
    users = get_user_model().objects.all()
    ret = []
    for u in users:
        dashboard, created = m.MessageLog.objects.get_or_create(owner=u)
        ret.append(dashboard)
    return ret


def create_threads_w_n_max_messages(n):
    users = get_user_model().objects.all()
    ret = []
    num_msgs = random.randrange(0, n)
    for u in users:
        job = return_random_model_instance(m.Job)
        thread_type = return_random_model_instance(m.ThreadType)

        thread, created = m.Thread.objects.get_or_create(
            gmail_thread_id=str(uuid.uuid4()),
            job_id=job,
            subject=str(uuid.uuid4()),
            thread_type=thread_type,
            time_received=timezone.now(),
            message_thread_initiator=u,
            accepted_answer=str(uuid.uuid4()),
        )
        ret.append(thread)
        for _ in range(num_msgs):
            message, mcreated = m.Message.objects.get_or_create(
                message_id=str(uuid.uuid4()),
                message_thread_id=thread,
                subject=str(uuid.uuid4()),
                body=str(uuid.uuid4()),
                to=str(uuid.uuid4()),
                fromm=str(uuid.uuid4()),
                cc=str(uuid.uuid4()),
            )

            m.Attachment.objects.get_or_create(
                message_id=message,
                gmail_attachment_id=str(uuid.uuid4()),
                filename=str(uuid.uuid4()),
            )
    return ret


def create_default_db_entries():
    return {
        "users": {
            "1": get_user_model().objects.get_or_create(email="test1", password=PASSWORD),
            "2": get_user_model().objects.get_or_create(email="test2", password=PASSWORD),
            "3": get_user_model().objects.get_or_create(email="test3", password=PASSWORD),
            "4": get_user_model().objects.get_or_create(email="test4", password=PASSWORD),
            "4": get_user_model().objects.get_or_create(email="test5", password=PASSWORD),
            "staff": get_user_model().objects.get_or_create(
                email="staff", password=PASSWORD, is_staff=True
            ),
            "admin": get_user_model().objects.get_or_create(
                email="admin", password=PASSWORD, is_staff=True, is_superuser=True
            ),
        },
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
        "dashboards": create_dashboards(),  # list of dashboard objects
        "threads": create_threads_w_n_max_messages(10),  # list of thread objects
    }


class ApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_get_messages_for_thread(self):
        threads = m.Thread.objects.all()
        for thread in threads:
            dashboard = m.MessageLog.objects.get(owner=thread.message_thread_initiator)
            url = reverse("api_get_all_thread_messages", args=[thread.gmail_thread_id])
            # unauthenticated user should get redirected
            redirect_auth_check(url, "", 302, redirect_join(USER_LOGIN, url))
            auth_check(url, "staff", 200)
            auth_check(url, "admin", 200)
            # owner of the dashboard should be able to see it
            response = auth_check(url, dashboard.owner.email, 200)
            messages = m.Message.objects.filter(message_thread_id=thread).values("pk")
            self.assertListEqual(
                [msg["pk"] for msg in messages],
                json_to_list(response.json()["data"], "pk"),
            )

    def test_get_unread_messages(self):
        url = reverse("gmail_get_unread_messages")
        basic_auth_check(url, "", 401)
        # user = get_user_model().objects.first()
        # TODO cannot test a successful auth of this view because of how
        # gmail access/refresh tokens are saved
        # basic_auth_check(url, user.email, 200)

    def test_notify_users_of_open_messages(self):
        url = reverse("notify_users_of_open_messages")
        basic_auth_check(url, "", 401)
        user = get_user_model().objects.first()
        basic_auth_check(url, user.email, 200)


class MessageManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()

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
            redirect_auth_check(url, "", 302, redirect_join(USER_LOGIN, url))

            # user who is not a super user or staff or owner of the dashboard
            # should get denied
            user = get_user_model().objects.all().exclude(email=dash.owner.email).first()
            auth_check(url, user.email, 403)

            auth_check(url, "staff", 200)
            auth_check(url, "admin", 200)
            # owner of the dashboard should be able to see it
            auth_check(url, dash.owner.email, 200)


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_thread_detailed(self):
        threads = m.Thread.objects.all()
        for thread in threads:
            url = reverse("admin:message_thread_detailed_view", args=[thread.id])

            # unauthenticated user should get redirected
            redirect_auth_check(url, "", 302, redirect_join(ADMIN_LOGIN, url))
            auth_check(url, "test1", 403)
            auth_check(url, "staff", 200)
            response = auth_check(url, "admin", 200)
            # https://docs.djangoproject.com/en/4.0/topics/testing/tools/
            # context is a list of contexts
            messages = m.Message.objects.filter(message_thread_id=thread)
            view_messages = from_context(response.context, "my_messages")
            difference = messages.difference(view_messages)
            self.assertEqual(
                difference.count(), 0, f"\n\ndifference: {difference.values_list()}"
            )

            attachments = m.Attachment.objects.filter(
                message_id__in=[m.id for m in messages]
            )
            view_attachments = from_context(response.context, "my_attachments")
            difference = attachments.difference(view_attachments)
            self.assertEqual(
                difference.count(), 0, f"\n\ndifference: {difference.values_list()}"
            )

    def test_resend_message_log_link(self):
        subject = "Thomas Builders Message Manager"
        from_email = settings.EMAIL_HOST_USER
        for message_log in m.MessageLog.objects.all():
            total_open_messages = m.Thread.objects.filter(
                message_thread_initiator=message_log.owner
            ).count()
            ctx = {
                "open_message_count": total_open_messages,
                "dashboard_link": settings.DOMAIN_URL
                + reverse("message_log_detailed", args=[message_log.slug]),
            }
            recipient_list = [message_log.owner.email]
            html_body = render_to_string("email_notifications/open_message.html", ctx)
            message_body = strip_tags(html_body)

            url = reverse("message_log_resend", args=[message_log.slug])
            # TODO the to fields of the emails are not matching
            redirect_auth_check(url, "", 302, redirect_join(ADMIN_LOGIN, url))
            auth_check(url, "test1", 403)
            auth_check(url, "staff", 200)
            auth_check(url, "admin", 200)
            email_message = mail.EmailMessage(
                subject, message_body, from_email=from_email, to=recipient_list
            )
            compare_emails(email_message, mail.outbox[0])
            mail.outbox.clear()

    def test_gmail_authorize(self):
        url = reverse("authorize_gmail_credentials")
        # unauthenticated user should get redirected
        redirect_auth_check(url, "", 302, redirect_join(ADMIN_LOGIN, url))
        auth_check(url, "test1", 403)
        auth_check(url, "staff", 403)
        auth_check(url, "admin", 302)  # should be a redirect to the google prompt
