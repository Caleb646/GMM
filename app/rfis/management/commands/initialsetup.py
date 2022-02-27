from dataclasses import dataclass
from django.core.management.base import BaseCommand
from django.contrib.auth.models import  Group, Permission
from django.contrib.auth import get_user_model
from django.conf import settings

from django.utils import timezone
from ...models import Job

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


class Command(BaseCommand):
    """
    Sets up all of the test groups, permissions, jobs, rfis, and users. Run after: python manage.py migrate
    """
    help = "Will create all groups, permissions, job, and user needed for testing"

    def handle(self, *args, **options):
        self._create_users()
        self._create_jobs()

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
            Job.objects.create(**j)