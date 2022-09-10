from django.contrib.auth.admin import UserAdmin

from .. import forms as f
from .. import models as m


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
        (
            "Permissions",
            {"fields": ("can_notify", "is_superuser", "is_staff", "is_active")},
        ),
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
