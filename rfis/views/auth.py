from django.contrib.auth import authenticate, login
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View

from .. import forms as f


class LoginView(View):

    template_name = "auth/login.html"

    def get(self, request, *args, **kwargs):
        form = f.LoginForm()
        if request.user.is_authenticated:
            return redirect(kwargs.get("next", "/"))
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        login_form = f.LoginForm(request.POST)
        if login_form.is_valid():
            username, password = (
                login_form.cleaned_data["username"],
                login_form.cleaned_data["password"],
            )
            if user := authenticate(request, username=username, password=password):
                login(request, user)
                return redirect(request.GET.get("next", "/"))
            login_form.add_error("username", "Username or password was incorrect.")

        return render(request, self.template_name, {"form": login_form})


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = "auth/reset_password.html"
    email_template_name = "email_notifications/reset_password.html"
    subject_template_name = "email_notifications/reset_password.txt"
    success_message = (
        "We've emailed you instructions for setting your password, if an account exists"
        " with the email you entered. You should receive them shortly. If you don't"
        " receive an email, please make sure you've entered the address you registered"
        " with, and check your spam folder."
    )
    success_url = reverse_lazy("base_user_reset_password")
