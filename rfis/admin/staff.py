from admin_searchable_dropdown.filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.html import format_html

from .. import forms as f
from .. import models as m
from . import common


class GmailCredentialsAdmin(admin.ModelAdmin):
    pass


class MyUserDashboardFilter(AutocompleteFilter):
    title = "User"  # display title
    field_name = "owner"  # name of the foreign key field


class DashboardAdmin(admin.ModelAdmin):
    search_fields = ["owner__startswith"]
    list_display = ("owner", "slug", "resend_button")
    list_filter = (MyUserDashboardFilter,)
    add_form = f.DashboardCreateForm
    form = f.DashboardChangeForm

    def resend_button(self, object: m.MessageLog):
        return format_html(
            f"<a href=javascript:api_request('{reverse('message_log_resend', args=[object.slug])}')>Resend</a>",
        )


class JobAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("name", "start_date")


class ThreadTypeAltNameInline(admin.StackedInline):
    model = m.ThreadTypeAltName
    extra = 0


class ThreadTypeAdmin(admin.ModelAdmin):
    # allows to create a message type with alternatives on
    # the message type create page
    inlines = [ThreadTypeAltNameInline]


class ThreadGroupAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("name",)


class ThreadTopicAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("name",)


class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "message_id",
        "subject",
        "fromm",
        "time_received",
    )


class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "message_id",
        "filename",
        "time_received",
    )


class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "codename",
        "content_type",
    )


admin.site.site_header = "Dashboard"
admin.site.site_title = "Dashboard"
admin.site.register(m.MyUser, common.MyUserAdmin)
admin.site.register(m.MessageLog, DashboardAdmin)
admin.site.register(m.Job, JobAdmin)
admin.site.register(m.ThreadType, ThreadTypeAdmin)
# admin.site.register(m.ThreadTypeAltName, MessageThreadTypeAlternativeNameAdmin)
admin.site.register(m.ThreadGroup, ThreadGroupAdmin)
admin.site.register(m.ThreadTopic, ThreadTopicAdmin)
admin.site.register(m.Thread)
admin.site.register(m.Message, MessageAdmin)
admin.site.register(m.Attachment, AttachmentAdmin)
admin.site.register(m.GmailCredentials, GmailCredentialsAdmin)

admin.site.register(Permission, PermissionAdmin)
