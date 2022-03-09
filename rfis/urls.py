from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.HomeView.as_view(), name="base_user_home_view"),
    path('login/', v.LoginView.as_view(), name="base_user_login"),
    path('dashboard/<slug:slug>/detailed/', v.DashboardView.as_view(), name="dashboard_detailed"),
    path('dashboard/<slug:slug>/resend/', v.resend_dashboard_link, name="dashboard_resend"),
    path('api/message-thread/<str:gmail_thread_id>/messages/', v.ThreadMessagesView.as_view(), name="api_get_all_thread_messages"),
    path('api/message/<str:message_id>/attachment/<str:attachment_id>/download/', v.AttachmentDownloadView.as_view(), name="gmail_message_attachment_download"),
    path('api/unread-messages/', v.gmail_get_unread_messages, name="gmail_get_unread_messages"),
    path('api/notify-users-open-messages/', v.notify_users_of_open_messages, name="notify_users_of_open_messages"),
    path('gmail-api/gmail-oauth-callback/', v.GmailOAuthCallback.as_view(), name="gmail_oauth_callback"),
    path('gmail-api/authorize/', v.GmailAuthorize.as_view(), name="authorize_gmail_credentials")
]