import os
import json
from time import sleep
import base64
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

from ..gmail_service import get_test_message, get_test_thread
from .. import constants as c, models as m, utils as u, gmail_service as g_service, email_parser as e_parser



class AttachmentDownloadView(View):

    def get(self, request, *args, **kwargs):
        message = m.Message.objects.get(message_id=kwargs["message_id"])
        attachment = m.Attachment.objects.get(message_id=message, gmail_attachment_id=kwargs["attachment_id"])
        gmail_service = g_service.GmailService()
        # layout {size: int, data: "base64encoded"}
        gmail_attachment = gmail_service.get_attachment(message.message_id, attachment.gmail_attachment_id)
        response = HttpResponse(base64.urlsafe_b64decode(gmail_attachment["data"]), headers={
            'Content-Type': 'application/vnd.ms-excel',
            'Content-Disposition': f"attachment; filename={attachment.filename}",
        })
        return response
