from admin_searchable_dropdown.views import AutocompleteJsonView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from .. import models as m


class JobSearchView(AutocompleteJsonView, LoginRequiredMixin):
    model_admin = None

    def get_queryset(self):
        return m.Job.objects.all().order_by("name")


class MyUserSearchView(AutocompleteJsonView, LoginRequiredMixin):
    model_admin = None

    def get_queryset(self):
        return m.MyUser.objects.all().order_by("email")


class ThreadDetailedView(LoginRequiredMixin, View):
    template_name = "admin/message_thread/detailed.html"
    login_url = reverse_lazy("user:login")

    def get(self, request, *args, **kwargs):
        message_thread = m.Thread.objects.get(pk=kwargs["pk"])
        messages = m.Message.objects.filter(message_thread_id=message_thread)
        attachments = m.Attachment.objects.filter(message_id__in=[m.id for m in messages])
        return render(
            request,
            self.template_name,
            {"my_messages": messages, "my_attachments": attachments},
        )
