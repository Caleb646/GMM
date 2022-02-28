from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html

from admin_searchable_dropdown.filters import AutocompleteFilter

from .basic_views import MessageThreadDetailedView
from .forms import MyUserCreateForm, MyUserChangeForm
from .models import MyUser, Job, MessageThread, Message, Attachment, Dashboard

from . import basic_views as v, forms as f, models as m


class MyUserAdmin(UserAdmin):

    add_form = f.MyUserCreateForm
    form = f.MyUserChangeForm
    model = m.MyUser
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
        ('Groups', {'fields': ('groups',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)


class DashboardAdmin(admin.ModelAdmin):
    search_fields = ['owner__startswith']
    list_display = ('owner', 'slug', 'detailed_view_button')
    add_form = f.DashboardCreateForm
    form = f.DashboardChangeForm

    def detailed_view_button(self, object: m.Dashboard):
        return format_html(
            f"<a href={reverse('dashboard_detailed', args=[object.slug])}>View</a>", 
        )


class JobAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'start_date')


class MessageThreadFilter(AutocompleteFilter):
    title = 'Job' # display title
    field_name = 'job_id' # name of the foreign key field


class MessageThreadAdmin(admin.ModelAdmin):
    search_fields = ('subject__startswith', )
    list_filter = (
            MessageThreadFilter,
            'thread_type',
            'thread_status',
        )
    list_display = (
            'job_id', 
            'message_thread_initiator', 
            'subject',
            "accepted_answer",
            'thread_status',
            'thread_type', 
            'due_date',
            'detailed_view_button'
        )

    change_list_template = "admin/message_thread/change_list.html"

    def detailed_view_button(self, object: m.MessageThread):
        return format_html(
            f"<a href={reverse('message_thread_detailed_view', args=[object.id])}>View</a>", 
        )

    def get_urls(self):
        urls = super().get_urls()
        # custom_urls have to be at the top of the list or django wont match them
        custom_urls = [
            path('<int:pk>/detailed/', v.MessageThreadDetailedView.as_view(), name="message_thread_detailed_view"),
        ]
        return custom_urls + urls


class MessageAdmin(admin.ModelAdmin):
    list_display = (
            'message_id', 
            'subject', 
            'fromm', 
            'time_received',
        )


class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
            'message_id', 
            'filename', 
            'time_received',
        )


admin.site.site_header = "Dashboard"
admin.site.site_title = "Dashboard"
admin.site.register(m.MyUser, MyUserAdmin)
admin.site.register(m.Dashboard, DashboardAdmin)
admin.site.register(m.Job, JobAdmin)
admin.site.register(m.MessageThread, MessageThreadAdmin)
admin.site.register(m.Message, MessageAdmin)
admin.site.register(m.Attachment, AttachmentAdmin)

# admin_site = MyAdminSite()
# admin_site.site_header = "Dashboard"
# admin_site.site_title = "Dashboard"
# admin_site.register(MyUser, MyUserAdmin)
# admin_site.register(Job, JobAdmin)
# admin_site.register(MessageThread, MessageThreadAdmin)
# admin_site.register(Message)
# admin_site.register(Attachment)



