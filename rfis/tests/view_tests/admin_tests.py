from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils.html import strip_tags

from ... import models as m
from .. import utils as testu


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = testu.create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_thread_detailed(self):
        threads = m.Thread.objects.all()
        for thread in threads:
            url = reverse("admin:message_thread_detailed_view", args=[thread.id])

            # unauthenticated user should get redirected
            testu.redirect_auth_check(
                url, "", 302, testu.redirect_join(testu.ADMIN_LOGIN, url)
            )
            testu.auth_check(url, "test1", 403)
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
            testu.redirect_auth_check(
                url, "", 302, testu.redirect_join(testu.ADMIN_LOGIN, url)
            )
            testu.auth_check(url, "test1", 403)
            testu.auth_check(url, "staff", 200)
            testu.auth_check(url, "admin", 200)
            email_message = mail.EmailMessage(
                subject, message_body, from_email=from_email, to=recipient_list
            )
            testu.compare_emails(email_message, mail.outbox[0])
            mail.outbox.clear()

    def test_gmail_authorize(self):
        url = reverse("authorize_gmail_credentials")
        # unauthenticated user should get redirected
        testu.redirect_auth_check(
            url, "", 302, testu.redirect_join(testu.ADMIN_LOGIN, url)
        )
        testu.auth_check(url, "test1", 403)
        testu.auth_check(url, "staff", 403)
        testu.auth_check(url, "admin", 302)  # should be a redirect to the google prompt
