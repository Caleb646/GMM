from django.contrib.auth import views as auth_views
from django.urls import path

from . import views as v

urlpatterns = [
    path("", v.HomeView.as_view(), name="base_user_home"),
    path("login/", v.LoginView.as_view(), name="base_user_login"),
    path(
        "reset-password/", v.ResetPasswordView.as_view(), name="base_user_reset_password"
    ),
    path(
        "reset-password-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/reset_password_confirm.html"
        ),
        name="base_user_reset_password_confirm",
    ),
    path(
        "reset-password-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/reset_password_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "message-log/<slug:slug>/detailed/",
        v.MessageLogView.as_view(),
        name="message_log_detailed",
    ),
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
