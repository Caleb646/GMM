from audioop import add
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.conf import settings

from .gmail_service import GmailService, add_unread_messages

class MyView(View):
    # form_class = MyForm
    # initial = {'key': 'value'}
    template_name = 'templates/rfis/test.html'

    def get(self, request, *args, **kwargs):
        # <view logic>
        return render(request, self.template_name, {"domain_url" : settings.DOMAIN_URL})

    def post(self, request, *args, **kwargs):
        # service = GmailService()
        # response = service.get_unread_messages()
        # full_message = service.get_message(response["messages"][0]["id"])
        # print(full_message, "full message")
        # return render(request, self.template_name, {"domain_url" : settings.DOMAIN_URL, "msg" : "Successfully post", "resp" : response, "message" : full_message})
        add_unread_messages()
        return render(request, self.template_name, {"domain_url" : settings.DOMAIN_URL, "msg" : "Successfully post"})

