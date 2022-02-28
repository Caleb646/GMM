from django.urls import path
from . import basic_views as v
from .views import api

urlpatterns = [
    path('dashboard/<slug:slug>/detailed/', v.DashboardView.as_view(), name="dashboard_detailed"),
    path('api/message/<str:message_id>/attachment/<str:attachment_id>/', api.AttachmentDownloadView.as_view(), name="gmail_message_attachment_download"),
    path('cron-api/unread-messages/', v.CronJobViews.gmail_get_unread_messages, name="gmail_get_unread_messages"),
    path('cron-api/notify-users-open-messages/', v.CronJobViews.notify_users_of_open_messages, name="notify_users_of_open_messages"),
    path('gmail-api/gmail-oauth-callback/', v.GmailOAuthCallback.as_view()),
    path('gmail-api/authorize/', v.GmailAuthorize.as_view(), name="authorize_gmail_credentials"),
]