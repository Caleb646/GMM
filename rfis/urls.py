from django.urls import path

from . import views as v

urlpatterns = [
    path(
        "message-log/<slug:slug>/resend/",
        v.MessageLogResendView.as_view(),
        name="message_log_resend",
    ),
    path(
        "api/settings/",  # form: ?key=setting-name
        v.SettingsView.as_view(),
        name="api_settings_get",
    ),
    path(
        "api/message-thread/<str:gmail_thread_id>/messages/",
        v.ThreadMessagesView.as_view(),
        name="api_get_all_thread_messages",
    ),
    path(
        "api/message/<str:message_id>/attachment/<str:attachment_id>/download/",
        v.AttachmentDownloadView.as_view(),
        name="gmail_message_attachment_download",
    ),
    path(
        "api/unread-messages/",
        v.gmail_get_unread_messages,
        name="gmail_get_unread_messages",
    ),
    path(
        "api/notify-users-open-messages/",
        v.notify_users_of_open_messages,
        name="notify_users_of_open_messages",
    ),
    path(
        "gmail-api/gmail-oauth-callback/",
        v.GmailOAuthCallback.as_view(),
        name="gmail_oauth_callback",
    ),
    path(
        "gmail-api/authorize/",
        v.GmailAuthorize.as_view(),
        name="authorize_gmail_credentials",
    ),
]
