from django.shortcuts import redirect, render
from django.urls import reverse


def bad_request(request, exception=None):
    return render(request, "errors/403.html")


def permission_denied(request, exception=None):
    return render(request, "errors/403.html")


def page_not_found(request, exception=None):  # redirect to homepage
    return redirect(reverse("user:index"))
    # return render(request, "errors/404.html")


def server_error(request, exception=None):  # redirect to homepage
    return redirect(reverse("user:index"))
    # return render(request, "errors/404.html")
