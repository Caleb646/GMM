import os
import json
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from .. import constants as c, models as m


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