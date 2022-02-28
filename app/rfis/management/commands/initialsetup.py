from dataclasses import dataclass
from django.core.management.base import BaseCommand
from django.contrib.auth.models import  Group, Permission
from django.contrib.auth import get_user_model
from django.conf import settings

from django.utils import timezone
from ...models import Job
from ... import constants as c

MyUser = get_user_model()

USERS = {
    MyUser.objects.create_superuser : [
            [{'email' : 'calebthomas646@yahoo.com', 'password' : settings.ADMIN_PASSWORD}, (None, None)],
        ],
    MyUser.objects.create_user : [
            [{'email' : settings.CRON_USER_NAME, 'password' : settings.CRON_USER_PASSWORD, "is_active": True}, (None, None)],
        ],
}

JOBS = [
    {"name" : settings.DEFAULT_JOB_NAME, "start_date" : timezone.now()},
    {"name" : "TestJob", "start_date" : timezone.now()}
]

GROUPS = {

    c.GROUP_NAME_STAFF_USERS: {
        # model specific permissions
        "myuser" : ["add","change","view"],
        "dashboard" : ["view"],
        "job" : ["add","delete","change","view"],
        "messagethread" : ["change","view"],
        "message": ["view"]
    },
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
            for app_model in GROUPS[group_name]:
                for permission_name in GROUPS[group_name][app_model]:
                    name = "Can {} {}".format(permission_name, app_model)
                    model_add_perm, created = Permission.objects.get_or_create(name=name)
                    new_group.permissions.add(model_add_perm)

    def _create_users(self, *args, **kwargs):
        for user_create_cmd in USERS:
            for user in USERS[user_create_cmd]:
                email = user[0]["email"]
                password = user[0]["password"]
                print(f"Attempting to create user: {email}")
                try:
                    user_create_cmd(email=email, password=password)
                except Exception as e:
                    print(f"Error while creating user: {email} -> {e}")
                    continue
                print("User created successfully")

    def _create_jobs(self):
        for j in JOBS:
            job, created = Job.objects.get_or_create(**j)