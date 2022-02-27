from django.urls import path
from . import views as v

urlpatterns = [
    path('dashboard/<slug:slug>/detailed/', v.DashboardView.as_view(), name="dashboard_detailed"),
    path('cron-api/unread-messages/', v.CronJobViews.gmail_get_unread_messages, name="gmail_get_unread_messages"),
    path('cron-api/notify-users-open-messages/', v.CronJobViews.notify_users_of_open_messages, name="notify_users_of_open_messages"),
    path('gmail-api/gmail-oauth-callback/', v.GmailOAuthCallback.as_view()),
    path('gmail-api/authorize/', v.GmailAuthorize.as_view(), name="authorize_gmail_credentials"),
]