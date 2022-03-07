import base64
from time import sleep
import dateparser
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.mail import send_mass_mail, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from constance import config

from .. import constants as c, models as m, utils as u, gmail_service as g_service, email_parser as e_parser


class AttachmentDownloadView(View):

    def get(self, request, *args, **kwargs):
        message = m.Message.objects.get(message_id=kwargs["message_id"])
        attachment = m.Attachment.objects.get(message_id=message, gmail_attachment_id=kwargs["attachment_id"])
        gmail_service = g_service.GmailService()
        # layout {size: int, data: "base64encoded"}
        gmail_attachment = gmail_service.get_attachment(message.message_id, attachment.gmail_attachment_id)
        return HttpResponse(
            base64.urlsafe_b64decode(gmail_attachment["data"]),
            headers={
                'Content-Type': 'application/vnd.ms-excel',
                'Content-Disposition': f"attachment; filename={attachment.filename}",
            },
        )

@login_required
def resend_dashboard_link(request, *args, **kwargs):
    dashboard = m.Dashboard.objects.get(slug=kwargs["slug"])
    total_open_messages = m.MessageThread.objects.filter(message_thread_initiator=dashboard.owner).count()
    ctx = {
        "open_message_count": total_open_messages, 
        "dashboard_link": settings.DOMAIN_URL + reverse("dashboard_detailed", args=[dashboard.slug])
        }
    message_body = render_to_string("email_notifications/open_message.html", ctx)
    send_mail("Thomas Builders Message Manager", strip_tags(message_body), html_message=message_body, from_email=settings.EMAIL_HOST_USER, recipient_list=[dashboard.owner.email])
    return JsonResponse({c.JSON_RESPONSE_MSG_KEY: "The notification was successfully sent."}, status=200)

###############################################################################################################################################################
#                                   These views are also used for cron operations
###############################################################################################################################################################

@u.logged_in_or_basicauth()
def gmail_get_unread_messages(request, *args, **kwargs):
    service = g_service.GmailService()
    g_parser = e_parser.GmailParser()
    unread_threads = service.get_threads()
    current_count = 0
    max_count_before_sleep = 25

    print("Getting unread messages")

    for thread_info in unread_threads:
        thread = service.get_thread(thread_info["id"])
        messages = thread.get("messages")
        if not messages:
            continue
        earliest_message_index = service.find_earliest_message_index(messages)
        # set the earliest message as the first message in the list
        # so the message_thread_initiator field will be set correctly
        if earliest_message_index != len(messages):
            earliest_message = messages[earliest_message_index]
            first_message = messages[0]
            earliest_message, first_message = first_message, earliest_message
        for msg in messages:
            current_count += 1
            #rate limit requests
            if current_count > max_count_before_sleep:
                current_count = 0
                sleep(0.25)
            created = u.create_db_entry_from_parser(g_parser, msg)
            if created:
                service.messages_read.append(g_parser.message_id)
    #TODO uncomment
    service.mark_read_messages()
    return JsonResponse({c.JSON_RESPONSE_MSG_KEY : f"{len(service.messages_read)} messages were added successfully."}, status=200)
   
@u.logged_in_or_basicauth()
def notify_users_of_open_messages(request, *args, **kwargs):
    #TODO only users with the can_notify will receive an email.
    # may need to change this with a setting in the future
    all_users = m.MyUser.objects.filter(can_notify=True) #u.get_users_with_permission("rfis.receive_notifications", include_su=False) 
    messages = []
    for user in all_users:
        user_dashboard, created = m.Dashboard.objects.get_or_create(owner=user)
        total_open_messages = m.MessageThread.objects.filter(message_thread_initiator=user).count()
        ctx = {
            "open_message_count": total_open_messages, 
            "dashboard_link": settings.DOMAIN_URL + reverse("dashboard_detailed", args=[user_dashboard.slug])
            }
        message_body = render_to_string("email_notifications/open_message.html", ctx)
        send_mail("Thomas Builders Message Manager", strip_tags(message_body), html_message=message_body, from_email=settings.EMAIL_HOST_USER, recipient_list=[user.email])
        #messages.append(("Thomas Builders Message Manager", message_body , settings.EMAIL_HOST_USER, [str(user.email)]))
    #send_mass_mail(messages, fail_silently=False)
    return JsonResponse({c.JSON_RESPONSE_MSG_KEY : "Notifications were successfully sent."}, status=200)

###############################################################################################################################################################
#                                   End cron views
###############################################################################################################################################################

