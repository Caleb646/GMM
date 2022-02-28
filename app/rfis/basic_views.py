import os
import json
from time import sleep
import dateparser
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.conf import settings
from django.forms import modelformset_factory
from django import forms
from django.core.mail import send_mass_mail, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.mixins import LoginRequiredMixin

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from .gmail_service import get_test_message, get_test_thread
from . import constants as c, models as m, utils as u, gmail_service as g_service, email_parser as e_parser,\
    formsets as f_sets


class CronJobViews:

    @staticmethod
    @u.logged_in_or_basicauth()
    def gmail_get_unread_messages(request, *args, **kwargs):
        service = g_service.GmailService()
        g_parser = e_parser.GmailParser()
        unread_threads = service.get_threads()
        current_count = 0
        max_count_before_sleep = 25

        print("getting unread messages")

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
                temp = earliest_message
                earliest_message = first_message
                first_message = temp

            for msg in messages:
                current_count += 1
                #rate limit requests
                if current_count > max_count_before_sleep:
                    current_count = 0
                    sleep(0.25)

                #print(f"\n\nraw gmail msg:\t {msg}\n\n")
                g_parser.parse(msg)
                # store message id so these messages can be marked as read later
                service.messages_read.append(g_parser.message_id)
                
                #print(f"\nmessage data: {g_parser.format_test_data('')}\n")

                #if not m.Message.objects.filter(message_id=g_parser.message_id).exists():
                    # TODO keep commented out unless getting test data
                    #create_test_data(msg, g_parser.format_test_data(), "gmail_test_data.json")


                job = m.Job.objects.get_or_unknown(g_parser.job_name)
                message_thread = m.MessageThread.objects.create_or_get(
                    g_parser.thread_id,
                    job_id=job,
                    thread_type=g_parser.thread_type,
                    subject=g_parser.subject,
                    message_thread_initiator=g_parser.fromm
                )
                time_message_received = dateparser.parse(g_parser.date, settings={'TIMEZONE': 'US/Eastern', 'RETURN_AS_TIMEZONE_AWARE': True})
                message = m.Message.objects.create_or_get(
                    g_parser.message_id,
                    message_thread_id=message_thread,
                    subject=g_parser.subject,
                    body=g_parser.body,
                    debug_unparsed_body=g_parser.debug_unparsed_body,
                    fromm=g_parser.fromm,
                    to=g_parser.to,
                    time_received=time_message_received
                )
                for f_info in g_parser.files_info:
                    attachment, created = m.Attachment.objects.get_or_create(
                        filename=f_info["filename"],
                        gmail_attachment_id=f_info["gmail_attachment_id"],
                        time_received=time_message_received,
                        message_id=message
                    )
        #TODO uncomment
        #service.mark_read_messages()
        return HttpResponse("Messages were added successfully", status=200)
   

    @staticmethod
    @u.logged_in_or_basicauth()
    def notify_users_of_open_messages(request, *args, **kwargs):
        all_users = m.MyUser.objects.all()
        messages = []
        for user in all_users:
            user_dashboard, created = m.Dashboard.objects.get_or_create(owner=user.email)
            total_open_messages = m.MessageThread.objects.filter(message_thread_initiator=user.email).count()
            ctx = {
                "open_message_count": total_open_messages, 
                "dashboard_link": settings.DOMAIN_URL + reverse("dashboard_detailed", args=[user_dashboard.slug])
                }
            message_body = render_to_string("email_notifications/open_message.html", ctx)
            send_mail("Thomas Builders Message Manager", strip_tags(message_body), html_message=message_body, from_email=settings.EMAIL_HOST_USER, recipient_list=[user.email])
            #messages.append(("Thomas Builders Message Manager", message_body , settings.EMAIL_HOST_USER, [str(user.email)]))
        #send_mass_mail(messages, fail_silently=False)
        return HttpResponse("Notifications were successfully sent", status=200)


class DashboardView(View):
    template_name = 'rfis/dashboard/detailed.html'

    def get(self, request, *args, **kwargs):
        dashboard = m.Dashboard.objects.get(slug=kwargs["slug"])
        if not dashboard:
            return HttpResponse("dasboard doesnt exist.")

        ThreadsFormset = modelformset_factory(
            m.MessageThread,
            formset=f_sets.MessageThreadFormSet,
            fields=("job_id", "subject", "accepted_answer", "thread_type", "thread_status"),
            widgets = {
                'accepted_answer': forms.Textarea(attrs={'rows':2, 'cols':35}),
                'subject': forms.Textarea(attrs={'rows':2, 'cols':35, 'readonly': 'readonly'}),
                },
            extra=0
        )
        formset = ThreadsFormset(queryset=m.MessageThread.objects.filter(
            thread_status=m.MessageThread.ThreadStatus.OPEN, 
            message_thread_initiator=dashboard.owner)
            )
        return render(request, self.template_name, {"formset" : formset})

    #TODO should create a ThreadsFormset class
    def post(self, request, *args, **kwargs):      
        ThreadsFormset = modelformset_factory(
            m.MessageThread,
            formset=f_sets.MessageThreadFormSet,
            fields=("job_id", "subject", "accepted_answer", "thread_type", "thread_status"),
            widgets = {
                'accepted_answer': forms.Textarea(attrs={'rows':2, 'cols':35}),
                'subject': forms.Textarea(attrs={'rows':2, 'cols':35, 'readonly': 'readonly'}),
                },
            extra=0
        )
        formset = ThreadsFormset(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
        return render(request, self.template_name, {"formset" : formset})

    
###################################################################
#               Admin Views
###################################################################
class MessageThreadDetailedView(LoginRequiredMixin, View):
    template_name = 'admin/message_thread/detailed.html'

    def get(self, request, *args, **kwargs):
        message_thread = m.MessageThread.objects.get(pk=kwargs["pk"])
        messages = m.Message.objects.filter(message_thread_id=message_thread)
        attachments = m.Attachment.objects.filter(message_id__in=[m.id for m in messages])
        return render(request, self.template_name, {"my_messages" : messages, "my_attachments" : attachments})


def load_credentials(filename):
    with open(os.path.join(settings.BASE_DIR, filename), "r") as f:
        return json.load(f)

def save_credentials(credentials: Credentials, filename):
    with open(os.path.join(settings.BASE_DIR, filename), "w") as f:
        f.write(credentials.to_json())


class GmailAuthorize(LoginRequiredMixin, View):

    def get(self, request, format=None):
        # If modifying these scopes
        flow = Flow.from_client_config(load_credentials(c.GMAIL_CLIENT_SECRET_FILENAME), scopes=c.GMAIL_API_SCOPES)
        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console. If this
        # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
        # error.
        flow.redirect_uri = c.GMAIL_REDIRECT_URI
        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type='offline',
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes='true')
        request.session[c.GMAIL_API_SESSION_STATE_FIELDNAME] = state
        return redirect(authorization_url)

###################################################################
#               End Admin Views
###################################################################


###################################################################
#               Gmail Api Callback View
###################################################################
class GmailOAuthCallback(View):

    def get(self, request, format=None):
        # Specify the state when creating the flow in the callback so that it can
        # verified in the authorization server response.    
        state = request.session.get(c.GMAIL_API_SESSION_STATE_FIELDNAME)
        #.GET returns the url query parameters as a key,value dict
        url_params = request.GET
        #if states dont match throw an error
        if state != url_params.get(c.GMAIL_API_SESSION_STATE_FIELDNAME) and state and url_params.get(c.GMAIL_API_SESSION_STATE_FIELDNAME):
            return HttpResponse("States do not match", status=401)
    
        flow = Flow.from_client_config(load_credentials(c.GMAIL_CLIENT_SECRET_FILENAME), scopes=c.GMAIL_API_SCOPES, state=state)
        flow.redirect_uri = c.GMAIL_REDIRECT_URI
        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        flow.fetch_token(code=url_params["code"])
        save_credentials(flow.credentials, c.GMAIL_API_CREDENTIALS_FILENAME)      
        return redirect(reverse("admin:login"))


###################################################################
#               End Gmail Api Callback View
###################################################################



