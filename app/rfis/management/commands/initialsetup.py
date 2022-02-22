from django.core.management.base import BaseCommand
from django.contrib.auth.models import  Group, Permission
from django.contrib.auth import get_user_model
from django.conf import settings

MyUser = get_user_model()

USERS = {
    MyUser.objects.create_superuser : [
            [{'email' : 'calebthomas646@yahoo.com', 'password' : settings.ADMIN_PASSWORD}, (None, None)],
        ],
}


class Command(BaseCommand):
    """
    Sets up all of the test groups, permissions, jobs, rfis, and users. Run after: python manage.py migrate
    """
    help = "Will create all groups, permissions, job, and user needed for testing"

    def handle(self, *args, **options):
        self._create_users()

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