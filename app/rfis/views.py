from audioop import add
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.conf import settings

from .gmail_service import add_unread_messages
from .models import MessageThread, Message

class MyView(View):
    # form_class = MyForm
    # initial = {'key': 'value'}
    template_name = 'rfis/test.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"domain_url" : settings.DOMAIN_URL})

    def post(self, request, *args, **kwargs):
        add_unread_messages()
        return render(request, self.template_name, {"domain_url" : settings.DOMAIN_URL, "msg" : "Successfully post"})



class MessageThreadDetailedView(View):
    template_name = 'rfis/detailed.html'

    def get(self, request, *args, **kwargs):
        message_thread = MessageThread.objects.get(pk=kwargs["pk"])
        messages = Message.objects.filter(message_thread_id=message_thread)
        return render(request, self.template_name, {"my_messages" : messages})
