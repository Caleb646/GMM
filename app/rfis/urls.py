from django.urls import path
from . import views as v


urlpatterns = [
    path('rfis/', v.MyView.as_view(), name="rfis"),
    path('gmail-api/gmail-oauth-callback/', v.GmailOAuthCallback.as_view()),
    path('gmail-api/authorize/', v.GmailAuthorize.as_view()),
]