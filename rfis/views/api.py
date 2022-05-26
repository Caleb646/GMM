import base64

from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import serializers
from django.core.mail import send_mail, send_mass_mail
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.views import View

from .. import constants as c
from .. import email_parser as e_parser
from .. import gmail_service as g_service
from .. import models as m
from .. import utils as u


class SettingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        allowed_settings = ["SUBJECT_LINE_PARSER_CONFIDENCE", "DEFAULT_TIMEZONE"]
        key = request.GET.get("key")
        if key and key in allowed_settings:
            return JsonResponse(
                {
                    c.JSON_RESPONSE_MSG_KEY: "Setting retrieved",
                    "data": config.__getattr__(key),
                },
                status=200,
            )
        return JsonResponse(
            {
                c.JSON_RESPONSE_MSG_KEY: (
                    f"Setting: {key} doesn't exist or isn't allowed to be queried"
                )
            },
            status=500,
        )


class ThreadMessagesView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, *args, **kwargs):
        thread = m.Thread.objects.get(gmail_thread_id=kwargs["gmail_thread_id"])
        messages = m.Message.objects.filter(message_thread_id=thread)
        messages_data = serializers.serialize(
            "json",
            messages,
            fields=(
                "message_id",
                "fromm",
                "to",
                "cc",
                "time_received",
                "body",
                "debug_unparsed_body",
            ),
        )
        attachments = m.Attachment.objects.filter(message_id__in=[m.id for m in messages])
        attachments_data = serializers.serialize(
            "json",
            attachments,
            fields=(
                "message_id",
                "gmail_attachment_id",
                "filename",
            ),
        )

        context = {"messages": messages_data, "attachments": attachments_data}
        return JsonResponse(
            {c.JSON_RESPONSE_MSG_KEY: "Messages retrieved successfully", "data": context},
            status=200,
        )

    def test_func(self):
        return True


class AttachmentDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        message = m.Message.objects.get(message_id=kwargs["message_id"])
        attachment = m.Attachment.objects.get(
            message_id=message, gmail_attachment_id=kwargs["attachment_id"]
        )
        gmail_service = g_service.GmailService()
        # layout {size: int, data: "base64encoded"}
        gmail_attachment = gmail_service.get_attachment(
            message.message_id, attachment.gmail_attachment_id
        )
        return HttpResponse(
            base64.urlsafe_b64decode(gmail_attachment["data"]),
            headers={
                "Content-Type": "application/vnd.ms-excel",
                "Content-Disposition": f"attachment; filename={attachment.filename}",
            },
            status=200,
        )


###############################################################################################################################################################
#                                   These views are also used for cron operations
###############################################################################################################################################################


@u.logged_in_or_basicauth()
def gmail_get_unread_messages(request, *args, **kwargs):
    service = g_service.GmailService()
    g_parser = e_parser.GmailParser()
    read_messages = u.process_multiple_gmail_threads(service, g_parser)
    service.mark_read_messages(read_messages)
    return JsonResponse(
        {
            c.JSON_RESPONSE_MSG_KEY: (
                f"{len(read_messages)} messages were added successfully."
            )
        },
        status=200,
    )


@u.logged_in_or_basicauth()
def notify_users_of_open_messages(request, *args, **kwargs):
    all_users = (
        get_user_model().objects.notifiable_users()
    )  # u.get_users_with_permission("rfis.receive_notifications", include_su=False)
    messages = []
    for user in all_users:
        total_open_messages = m.Thread.objects.open_messages(user).count()
        if total_open_messages == 0:  # only send an email to users with open messages
            continue
        user_dashboard, created = m.MessageLog.objects.get_or_create(owner=user)
        ctx = {
            "open_message_count": total_open_messages,
            "dashboard_link": c.OPEN_MESSAGES_URL,
        }
        message_body = render_to_string("email_notifications/open_message.html", ctx)
        send_mail(
            "Thomas Builders Message Manager",
            strip_tags(message_body),
            html_message=message_body,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        # messages.append(("Thomas Builders Message Manager", message_body , settings.EMAIL_HOST_USER, [str(user.email)]))
    # send_mass_mail(messages, fail_silently=False)
    return JsonResponse(
        {c.JSON_RESPONSE_MSG_KEY: "Notifications were successfully sent."}, status=200
    )


###############################################################################################################################################################
#                                   End cron views
###############################################################################################################################################################
