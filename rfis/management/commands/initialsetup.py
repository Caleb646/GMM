from dataclasses import dataclass
from django.core.management.base import BaseCommand
from django.contrib.auth.models import  Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import django

from ... import constants as c, models as m

USERS = [
    # super users
    {
        'email' : settings.ADMIN_EMAIL, 
        'password' : settings.ADMIN_PASSWORD, 
        'is_superuser': True, 
        'is_staff': True, 
        "is_active": True,
    },
    # regulars users
    {
        'email' : settings.CRON_USER_NAME, 
        'password' : settings.CRON_USER_PASSWORD, 
        "is_active": True, 
    }
]

JOBS = [
    {"name" : c.FIELD_VALUE_UNKNOWN_JOB, "start_date" : timezone.now()},
    {"name" : "TestJob", "start_date" : timezone.now()}
]

GROUPS = {

    c.GROUP_NAME_STAFF_USERS: { 
        "rfis" : {
            #"myuser" : ["add","change","view"],
            "dashboard" : ["view"],
            "job" : ["add","delete","change","view"],
            "messagethread" : ["change","view"],
            "message": ["view"],
        },
    },
    c.GROUP_NAME_RECEIVE_NOTIFICATIONS_USERS: { 
        "rfis" : {
            "notifications": ["receive"]
        },
    }
}


class Command(BaseCommand):
    """
    Sets up all of the test groups, permissions, jobs, rfis, and users. Run after: python manage.py migrate
    """
    help = "Will create all groups, permissions, job, and user needed for testing"

    def handle(self, *args, **options):
        self._create_groups()
        self._create_users()
        self._create_jobs()

    def _create_groups(self):
        """
        Creates all of the groups and their specific permissions
        """
        for group_name in GROUPS:
            new_group, created = Group.objects.get_or_create(name=group_name)
            for app_name in GROUPS[group_name]:
                for model_name in GROUPS[group_name][app_name]:
                    for permission_name in GROUPS[group_name][app_name][model_name]:
                        name = f"Can {permission_name} {model_name}"
                        codename = f"{permission_name}_{model_name}"
                        content_type, created = ContentType.objects.get_or_create(app_label=app_name, model=model_name)
                        model_add_perm, created = Permission.objects.get_or_create(codename=codename, content_type=content_type)
                        new_group.permissions.add(model_add_perm)
                        print(f"Permission: {codename} added to {group_name} group")

    def _create_users(self, *args, **kwargs):
        for user_info in USERS:
            try:
                user, created = get_user_model().objects.get_or_create(**user_info)
                print(f"User: {user_info.get('email')} created successfully")
                continue
            except django.db.utils.IntegrityError:
                continue
            raise
            
    def _create_jobs(self):
        for j in JOBS:
            job, created = m.Job.objects.get_or_create(**j)
            print(f"Job: {j.get('name')} created successfully")