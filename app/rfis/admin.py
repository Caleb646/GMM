from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import MyUserCreateForm, MyUserChangeForm
from .models import MyUser, Job, MessageThread, Message, Attachment


class MyUserAdmin(UserAdmin):

    add_form = MyUserCreateForm
    form = MyUserChangeForm
    model = MyUser
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
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


admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Job)
admin.site.register(MessageThread)
admin.site.register(Message)
admin.site.register(Attachment)
