from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.views import View

from .. import forms as f

class LoginView(View):

    template_name = "auth/login.html"

    def get(self, request, *args, **kwargs):
        form = f.LoginForm()
        if request.user.is_authenticated:
            return redirect(kwargs.get("next", "/"))
        return render(request, self.template_name, {"form" : form})

    def post(self, request, *args, **kwargs):
        login_form = f.LoginForm(request.POST)
        if login_form.is_valid():
            username, password = login_form.cleaned_data["username"], login_form.cleaned_data["password"]
            if user := authenticate(request, username=username, password=password):
                login(request, user)
                return redirect(request.GET.get("next", "/"))
            login_form.add_error("username", "Username or password was incorrect.")

        return render(request, self.template_name, {"form" : login_form})
