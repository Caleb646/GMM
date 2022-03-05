from django.urls import path
from .views import api, admin as admin_v, messages as messages_v

urlpatterns = [
    path('dashboard/<slug:slug>/detailed/', messages_v.DashboardView.as_view(), name="dashboard_detailed"),
    path('dashboard/<slug:slug>/resend/', api.resend_dashboard_link, name="dashboard_resend"),
    path('api/message/<str:message_id>/attachment/<str:attachment_id>/download/', api.AttachmentDownloadView.as_view(), name="gmail_message_attachment_download"),
    path('api/unread-messages/', api.gmail_get_unread_messages, name="gmail_get_unread_messages"),
    path('api/notify-users-open-messages/', api.notify_users_of_open_messages, name="notify_users_of_open_messages"),
    path('gmail-api/gmail-oauth-callback/', admin_v.GmailOAuthCallback.as_view(), name="gmail_oauth_callback"),
    path('gmail-api/authorize/', admin_v.GmailAuthorize.as_view(), name="authorize_gmail_credentials")
]