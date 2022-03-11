from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html

from admin_searchable_dropdown.filters import AutocompleteFilter

from . import forms as f, models as m, views as v


class MyUserAdmin(UserAdmin):

    add_form = f.MyUserCreateForm
    form = f.MyUserChangeForm
    model = m.MyUser
    list_display = (
        "email",
        "can_notify",
        "is_superuser",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "groups",
        "can_notify",
        "is_superuser",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("can_notify", "is_superuser", "is_staff", "is_active")}),
        ("Groups", {"fields": ("groups",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "groups",
                    "can_notify",
                    "is_superuser",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email__startswith",)
    ordering = ("email", "groups")


class MyUserDashboardFilter(AutocompleteFilter):
    title = "User"  # display title
    field_name = "owner"  # name of the foreign key field


class MyUserMessageThreadFilter(AutocompleteFilter):
    title = "User"  # display title
    field_name = "message_thread_initiator"  # name of the foreign key field


class DashboardAdmin(admin.ModelAdmin):
    search_fields = ["owner__startswith"]
    list_display = ("owner", "slug", "detailed_view_button", "resend_button")
    list_filter = (MyUserDashboardFilter,)
    add_form = f.DashboardCreateForm
    form = f.DashboardChangeForm

    def detailed_view_button(self, object: m.MessageLog):
        return format_html(
            f"<a href={reverse('message_log_detailed', args=[object.slug])}>View</a>",
        )

    def resend_button(self, object: m.MessageLog):
        return format_html(
            f"<a href=javascript:fetch('{reverse('message_log_resend', args=[object.slug])}')>Resend</a>",
        )


class JobAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("name", "start_date")


class MessageThreadTypeAlternativeNameInline(admin.StackedInline):
    model = m.ThreadTypeAltName
    extra = 0


class MessageThreadTypeAdmin(admin.ModelAdmin):
    # allows to create a message type with alternatives on
    # the message type create page
    inlines = [MessageThreadTypeAlternativeNameInline]


class MessageThreadJobFilter(AutocompleteFilter):
    title = "Job"  # display title
    field_name = "job_id"  # name of the foreign key field


class MessageThreadAdmin(admin.ModelAdmin):
    search_fields = ("subject__startswith",)
    list_filter = (
        MessageThreadJobFilter,
        MyUserMessageThreadFilter,
        "time_received",
        "thread_type",
        "thread_status",
    )
    list_display = (
        "job_id",
        "message_thread_initiator",
        "subject",
        "accepted_answer",
        "thread_status",
        "thread_type",
        "time_received",
        "due_date",
        "detailed_view_button",
    )

    change_list_template = "admin/message_thread/change_list.html"

    def detailed_view_button(self, object: m.Thread):
        return format_html(
            f"<a href={reverse('admin:message_thread_detailed_view', args=[object.id])}>View</a>",
        )

    def get_urls(self):
        urls = super().get_urls()
        # custom_urls have to be at the top of the list or django wont match them
        custom_urls = [
            path("<int:pk>/detailed/", v.ThreadDetailedView.as_view(), name="message_thread_detailed_view"),
        ]
        return custom_urls + urls


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
admin.site.register(m.MyUser, MyUserAdmin)
admin.site.register(m.MessageLog, DashboardAdmin)
admin.site.register(m.Job, JobAdmin)
admin.site.register(m.ThreadType, MessageThreadTypeAdmin)
# admin.site.register(m.ThreadTypeAltName, MessageThreadTypeAlternativeNameAdmin)
admin.site.register(m.Thread, MessageThreadAdmin)
admin.site.register(m.Message, MessageAdmin)
admin.site.register(m.Attachment, AttachmentAdmin)

admin.site.register(Permission, PermissionAdmin)

# admin_site = MyAdminSite()
# admin_site.site_header = "MessageLog"
# admin_site.site_title = "MessageLog"
# admin_site.register(MyUser, MyUserAdmin)
# admin_site.register(Job, JobAdmin)
# admin_site.register(Thread, MessageThreadAdmin)
# admin_site.register(Message)
# admin_site.register(Attachment)
