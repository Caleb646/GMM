from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from .. import constants as c
from .. import formsets as f_sets
from .. import models as m
from .. import utils as u


class HomeView(LoginRequiredMixin, View):
    template_name = "message_manager/index.html"

    def get(self, request, *args, **kwargs):
        message_log = m.MessageLog.objects.filter(owner=request.user).first()
        return render(request, self.template_name, {"message_log": message_log})


class MessageLogView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "message_manager/message_log/detailed.html"

    def get(self, request, *args, **kwargs):
        dashboard = get_object_or_404(m.MessageLog, slug=kwargs["slug"])
        formset = f_sets.MessageThreadFormSet(
            queryset=m.Thread.objects.filter(
                thread_status=m.Thread.ThreadStatus.OPEN,
                message_thread_initiator=dashboard.owner,
            )
        ).create_model_formset()
        return render(request, self.template_name, {"formset": formset})

    def post(self, request, *args, **kwargs):
        formset = f_sets.MessageThreadFormSet().create_model_formset(
            request_post=request.POST, request_files=request.FILES
        )
        if formset.is_valid():
            formset.save()
        return render(request, self.template_name, {"formset": formset})

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        if self.request.user.is_staff:
            return True
        if self.request.user.has_perm("rfis.view_dashboard"):
            return True
        # the owner of the dashboard needs to match the request user
        if m.MessageLog.objects.get(slug=self.kwargs["slug"]).owner == self.request.user:
            return True
        return False
