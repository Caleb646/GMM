import base64
import json
from http.cookies import SimpleCookie
from urllib.parse import urljoin

from django.core import mail
from django.test import Client
from django.urls import reverse_lazy

from .universal_utils import PASSWORD

ADMIN_LOGIN = reverse_lazy("admin:login")
USER_LOGIN = reverse_lazy("base_user_login")
client = Client()


def email_password_to_http_auth(email):
    return base64.b64encode(bytes(f"{email}:{PASSWORD}", "utf8")).decode("utf8")


def auth_check(url, email, status_code):
    client.login(email=email, password=PASSWORD)
    response = client.get(url, follow=True)
    client.logout()
    if response.redirect_chain:
        assert any(status_code in route for route in response.redirect_chain), (
            f"Redirect chain {response.redirect_chain} != Target code: {status_code} on"
            f" {url}"
        )
    else:
        assert (
            response.status_code == status_code
        ), f"Response code {response.status_code} != Target code: {status_code} on {url}"
    return response


def basic_auth_check(url, email, status_code):
    client.defaults["HTTP_AUTHORIZATION"] = f"Basic {email_password_to_http_auth(email)}"
    response = client.get(url, follow=True)
    client.defaults["HTTP_AUTHORIZATION"] = SimpleCookie()
    assert (
        response.status_code == status_code
    ), f"Response code {response.status_code} != Target code: {status_code} on {url}"


def redirect_join(to, fromm):
    return urljoin(str(to), f"?next={str(fromm)}")


def redirect_auth_check(url, email, status_code, redirect_url):
    response = auth_check(url, email, status_code)
    found = any(redirect_url in route for route in response.redirect_chain)
    assert (
        found
    ), f"Target Redirect: {redirect_url} not in Redirect Chain: {response.redirect_chain}"


def from_context(context, key):
    if isinstance(context, dict):
        return context.get(key)
    elif not context:
        return None
    for ctx in context:
        if value := from_context(ctx, key):
            return value


def json_to_list(data, key):
    data = json.loads(data)
    return [d[key] for d in data]


def compare_emails(one: mail.EmailMessage, two: mail.EmailMessage):
    assert one.subject == two.subject, f"one: {one.subject} != two: {two.subject}"
    assert one.body == two.body, f"one: {one.body} != two: {two.body}"
    assert one.to == two.to, f"one: {one.to} != two: {two.to}"
    assert (
        one.from_email == two.from_email
    ), f"one: {one.from_email} != two: {two.from_email}"
