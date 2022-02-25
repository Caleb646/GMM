from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html

from admin_searchable_dropdown.filters import AutocompleteFilter

from .views import MessageThreadDetailedView
from .forms import MyUserCreateForm, MyUserChangeForm
from .models import MyUser, Job, MessageThread, Message, Attachment


class MyUserAdmin(UserAdmin):

    add_form = MyUserCreateForm
    form = MyUserChangeForm
    model = MyUser
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
            'thread_status',
            'thread_type', 
            'due_date',
            'detailed_view_button'
        )

    def detailed_view_button(self, object):
        return format_html(
            f"<a href={reverse('admin:message_thread_detailed_view', args=[object.id])}>View</a>", 
        )

    def get_urls(self):
        urls = super().get_urls()
        # custom_urls have to be at the top of the list or django wont match them
        custom_urls = [
            path('<int:pk>/detail-view/', MessageThreadDetailedView.as_view(), name="message_thread_detailed_view"),
        ]
        return custom_urls + urls


class MessageAdmin(admin.ModelAdmin):
    list_display = (
            'message_id', 
            'subject', 
            'fromm', 
            'time_received',
        )


admin.site.site_header = "Dashboard"
admin.site.site_title = "Dashboard"
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(MessageThread, MessageThreadAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Attachment)

# admin_site = MyAdminSite()
# admin_site.site_header = "Dashboard"
# admin_site.site_title = "Dashboard"
# admin_site.register(MyUser, MyUserAdmin)
# admin_site.register(Job, JobAdmin)
# admin_site.register(MessageThread, MessageThreadAdmin)
# admin_site.register(Message)
# admin_site.register(Attachment)



