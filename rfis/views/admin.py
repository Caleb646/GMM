from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from google_auth_oauthlib.flow import Flow

from .. import constants as c, models as m, gmail_service


class MessageThreadDetailedView(LoginRequiredMixin, View):
    template_name = 'admin/message_thread/detailed.html'

    def get(self, request, *args, **kwargs):
        message_thread = m.MessageThread.objects.get(pk=kwargs["pk"])
        messages = m.Message.objects.filter(message_thread_id=message_thread)
        attachments = m.Attachment.objects.filter(message_id__in=[m.id for m in messages])
        return render(request, self.template_name, {"my_messages" : messages, "my_attachments" : attachments})

class GmailAuthorize(LoginRequiredMixin, View):
    def get(self, request, format=None):
        # If modifying these scopes
        flow = Flow.from_client_config(gmail_service.GmailService.load_client_secret_config_f_file(), scopes=c.GMAIL_API_SCOPES)
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
        state_to_match = request.GET.get(c.GMAIL_API_SESSION_STATE_FIELDNAME)
        #if states dont match throw an error
        #print(f"google state: {state}\n\nmy state: {state_to_match}")
        # if state != state_to_match and state and state_to_match:
        #     return HttpResponse("States do not match", status=401)

        flow = Flow.from_client_config(gmail_service.GmailService.load_client_secret_config_f_file(), scopes=c.GMAIL_API_SCOPES, state=state)
        flow.redirect_uri = c.GMAIL_REDIRECT_URI
        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        flow.fetch_token(code=request.GET["code"])
        gmail_service.GmailService.save_client_token(flow.credentials)     
        return redirect(reverse("admin:login"))
