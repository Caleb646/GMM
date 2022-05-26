from admin_searchable_dropdown.views import AutocompleteJsonView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from .. import models as m


class JobSearchView(AutocompleteJsonView, LoginRequiredMixin):
    model_admin = None

    def get_queryset(self):
        if field_value := self.request.GET.get("term"):
            return m.Job.objects.filter(**{"name__icontains": field_value}).order_by(
                "name"
            )
        return m.Job.objects.all().order_by("name")


class MyUserSearchView(AutocompleteJsonView, LoginRequiredMixin):
    model_admin = None

    def get_queryset(self):
        # sourcery skip: assign-if-exp, reintroduce-else, swap-if-expression
        if not (
            self.request.user.is_superuser or self.request.user.is_staff
        ):  # only super or staff users can search by user
            return m.MyUser.objects.none()
        if field_value := self.request.GET.get("term"):
            field_name = "email__icontains"
            return m.MyUser.objects.filter(**{field_name: field_value}).order_by("email")
        return m.MyUser.objects.all().order_by("email")


class ThreadDetailedView(LoginRequiredMixin, View):
    template_name = "admin/message_thread/detailed.html"
    login_url = reverse_lazy("user:login")

    def get(self, request, *args, **kwargs):
        message_thread = m.Thread.objects.get(pk=kwargs["pk"])
        messages = m.Message.objects.filter(message_thread_id=message_thread)
        # older threads have duplicated attachments.
        # using distinct here removes the duplicates from those older threads.
        attachments = (
            m.Attachment.objects.filter(message_id__in=[m.id for m in messages])
            .order_by("gmail_attachment_id")
            .distinct("gmail_attachment_id")
        )
        return render(
            request,
            self.template_name,
            {"my_messages": messages, "my_attachments": attachments},
        )
