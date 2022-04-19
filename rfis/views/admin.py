import dateparser
from admin_searchable_dropdown.views import AutocompleteJsonView
from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import serializers
from django.core.mail import send_mail, send_mass_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.html import strip_tags
from django.views import View
from google_auth_oauthlib.flow import Flow

from .. import constants as c
from .. import gmail_service
from .. import models as m


class MessageLogResendView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("admin:login")

    def get(self, request, *args, **kwargs):
        dashboard = m.MessageLog.objects.get(slug=kwargs["slug"])
        total_open_messages = m.Thread.objects.open_messages(dashboard.owner).count()
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
            recipient_list=[dashboard.owner.email],
        )
        return JsonResponse(
            {c.JSON_RESPONSE_MSG_KEY: "The notification was successfully sent."},
            status=200,
        )

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


class GmailAuthorize(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("admin:login")

    def get(self, request, format=None):
        # If modifying these scopes
        flow = Flow.from_client_config(
            gmail_service.GmailService.load_client_secret_file(),
            scopes=c.GMAIL_API_SCOPES,
        )
        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console. If this
        # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
        # error.
        flow.redirect_uri = c.GMAIL_REDIRECT_URI
        authorization_url, state = flow.authorization_url(
            # this forces oauth to return a refresh token on each sign in
            prompt="consent",
            # approval_prompt="force",
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type="offline",
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes="true",
        )
        request.session[c.GMAIL_API_SESSION_STATE_FIELDNAME] = state
        return redirect(authorization_url)

    def test_func(self):  # only super users can change the gmail credentials
        return self.request.user.is_superuser  # or self.request.user.is_staff


class GmailOAuthCallback(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, format=None):
        # Specify the state when creating the flow in the callback so that it can
        # verified in the authorization server response.
        state = request.session.get(c.GMAIL_API_SESSION_STATE_FIELDNAME)
        # .GET returns the url query parameters as a key,value dict
        state_to_match = request.GET.get(c.GMAIL_API_SESSION_STATE_FIELDNAME)
        # if states dont match throw an error
        # print(f"google state: {state}\n\nmy state: {state_to_match}")
        if state != state_to_match and state and state_to_match:
            return HttpResponse("States do not match", status=401)

        flow = Flow.from_client_config(
            gmail_service.GmailService.load_client_secret_file(),
            scopes=c.GMAIL_API_SCOPES,
            state=state,
        )
        flow.redirect_uri = c.GMAIL_REDIRECT_URI
        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        flow.fetch_token(code=request.GET["code"])
        assert flow.credentials.refresh_token, "Refresh token has to be present"
        gmail_service.GmailService.save_client_token(flow.credentials)
        return redirect(reverse("admin:login"))

    def test_func(self):  # only super users can change the gmail credentials
        return self.request.user.is_superuser  # or self.request.user.is_staff
