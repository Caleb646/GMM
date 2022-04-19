from functools import partial

from admin_searchable_dropdown.filters import AutocompleteFilter
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from .. import constants as c
from .. import models as m
from .. import views as v
from . import common


class ThreadForm(forms.ModelForm):
    def clean(self):
        job = self.cleaned_data.get("job_id")  # an instance of the Job model
        accepted_answer = self.cleaned_data.get("accepted_answer")
        thread_type = self.cleaned_data.get("thread_type")
        thread_status = self.cleaned_data.get("thread_status")
        # if a thread is going to be closed then the above values have to be set correctly
        if thread_status == c.FIELD_VALUE_CLOSED_THREAD_STATUS:
            if job.name == c.FIELD_VALUE_UNKNOWN_JOB:
                raise ValidationError(
                    f"Job name cannot be {c.FIELD_VALUE_UNKNOWN_JOB} when closing a"
                    " message."
                )
            if thread_type == c.FIELD_VALUE_UNKNOWN_THREAD_TYPE:
                raise ValidationError(
                    "The thread type cannot be"
                    f" {c.FIELD_VALUE_UNKNOWN_THREAD_TYPE} when closing a message."
                )
            if not accepted_answer or accepted_answer == "":
                raise ValidationError(
                    "The accepted answer has to be filled out when closing a message."
                    " If an accepted answer is not applicable type N/A in the field."
                )
        return super().clean()


class UserThreadFilter(AutocompleteFilter):
    title = "User"  # display title
    field_name = "message_thread_initiator"  # name of the foreign key field

    def get_autocomplete_url(self, request, model_admin):
        return reverse("user:search_user")


class ThreadJobFilter(AutocompleteFilter):
    title = "Job"  # display title
    field_name = "job_id"  # name of the foreign key field

    def get_autocomplete_url(self, request, model_admin):
        return reverse("user:search_job")


class ThreadAdmin(admin.ModelAdmin):
    form = ThreadForm
    search_fields = (
        "subject__search",
        "message__vector_body_column",
    )
    list_filter = (
        ThreadJobFilter,
        UserThreadFilter,
        "time_received",
        "thread_type",
        "thread_status",
    )
    list_display = (
        "id",
        "job_id",
        "message_thread_initiator",
        "subject",
        "accepted_answer",
        "thread_status",
        "thread_type",
        "time_received",
        "detailed_view_button",
    )
    readonly_fields = [
        "gmail_thread_id",
    ]
    list_editable = ("job_id", "accepted_answer", "thread_status", "thread_type")
    change_list_template = "admin/message_thread/change_list.html"

    def get_changelist_form(self, request, **kwargs):
        """
        Return a ThreadForm class for use in the Formset on the changelist page.
        """
        defaults = {
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
            "fields": forms.ALL_FIELDS,
            "widgets": {
                "gmail_thread_id": forms.HiddenInput(
                    attrs={"required": False}
                ),  # adds a hidden field for js ids
                "accepted_answer": forms.Textarea(attrs={"rows": 2, "cols": 35}),
                "subject": forms.Textarea(
                    attrs={"rows": 2, "cols": 35, "readonly": "readonly"}
                ),
                "time_received": forms.DateTimeInput(
                    attrs={"readonly": "readonly"}, format="%m/%d/%y"
                ),
            },
            **kwargs,
        }
        return modelform_factory(self.model, ThreadForm, **defaults)

    def get_queryset(self, request):
        """
        Return a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        if (
            request.user.is_superuser or request.user.is_staff
        ) and request.user.is_active:
            return m.Thread.objects.all()
        if (
            not request.user.is_superuser and not request.user.is_staff
        ) and request.user.is_active:
            return m.Thread.objects.filter(message_thread_initiator=request.user)
        else:
            raise ValidationError(
                "Queryset could not be returned because user didn't meet requirements of"
                " being staff/super user or active."
            )

    def detailed_view_button(self, object: m.Thread):
        return format_html(
            f"<a href={reverse('user:message_thread_detailed_view', args=[object.id])}>View</a>",
        )

    def get_urls(self):
        urls = super().get_urls()
        # custom_urls have to be at the top of the list or django wont match them
        custom_urls = [
            path(
                "<int:pk>/detailed/",
                v.ThreadDetailedView.as_view(),
                name="message_thread_detailed_view",
            ),
            path(
                "search/user/",
                v.MyUserSearchView.as_view(model_admin=self),
                name="search_user",
            ),
            path(
                "search/job/",
                v.JobSearchView.as_view(model_admin=self),
                name="search_job",
            ),
        ]
        return custom_urls + urls


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
    # index_template = "user/index.html"
    login_form = UserAdminAuthenticationForm

    def has_permission(self, request):
        """
        Removed check for is_staff.
        """
        return request.user.is_active


class ThreadTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


class JobAdmin(admin.ModelAdmin):
    list_display = ("name",)


user_admin_site = MyUserAdminSite(name="user")
user_admin_site.register(m.Thread, ThreadAdmin)
user_admin_site.register(m.ThreadType, ThreadTypeAdmin)
user_admin_site.register(m.Job, JobAdmin)
user_admin_site.register(m.MyUser, common.MyUserAdmin)
