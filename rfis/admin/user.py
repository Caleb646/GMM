from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _

from .. import models as m
from . import common


class UserAdminAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                _("This account is inactive."),
                code="inactive",
            )


class MyUserAdminSite(AdminSite):
    site_header = "User Dashboard"
    site_title = "User Dashboard"
    index_template = "user/base.html"
    login_form = UserAdminAuthenticationForm

    def has_permission(self, request):
        """
        Removed check for is_staff.
        """
        return request.user.is_active


class MyUserAdmin(UserAdmin):
    model = m.MyUser
    list_display = ("email",)
    ordering = ("email", "groups")


class ThreadTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


class JobAdmin(admin.ModelAdmin):
    list_display = ("name",)


user_admin_site = MyUserAdminSite(name="usersadmin")

user_admin_site.register(m.Thread, common.ThreadAdmin)
user_admin_site.register(m.ThreadType, ThreadTypeAdmin)
user_admin_site.register(m.Job, JobAdmin)
