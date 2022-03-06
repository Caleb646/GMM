from django.contrib.auth.base_user import BaseUserManager
import uuid

from . import constants as c


class MyUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **kwargs):
        """
        Create and save a User with the given email and password.
        """  
        if not email or not password:
            raise ValueError(('Email and password must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        
        return user

    def create_superuser(self, email, password, **kwargs):
        """
        Create and save a SuperUser with the given email and password.
        """
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)
        return self.create_user(email, password, **kwargs)

    def get_or_create_unknown_user(self, email, *args, **kwargs):
        if self.filter(email=email).exists():
            return self.get(email=email)
        return self.create_user(email, str(uuid.uuid4()), **kwargs)

    def get_or_create(self, *args, **kwargs):
        if self.filter(email=kwargs.get("email")).exists():
            return (self.get(email=kwargs.get("email")), False)
        return (self.create_user(**kwargs), True)

    def reset_password(self, password):
        self.set_password(password)
        self.save()


class JobManager(BaseUserManager):

    def get_or_unknown(self, name, **kwargs):
        if self.all().filter(name=name).exists():
            return self.get(name=name)
        return self.get(name=c.FIELD_VALUE_UNKNOWN_JOB)   

    def get_or_create(self, *args, **kwargs):
        if self.filter(name=kwargs.get("name")).exists():
            return (self.get(name=kwargs.get("name")), False)
        return (self.create(**kwargs), True)    
        
class MessageThreadManager(BaseUserManager):

    def create_or_get(self, gmail_thread_id, **kwargs):       
        if self.all().filter(gmail_thread_id=gmail_thread_id).exists():
            return self.get(gmail_thread_id=gmail_thread_id)
        return self.create(gmail_thread_id=gmail_thread_id, **kwargs)

class MessageManager(BaseUserManager):

    def create_or_get(self, message_id, **kwargs):       
        if self.all().filter(message_id=message_id).exists():
            return self.get(message_id=message_id)
        return self.create(message_id=message_id, **kwargs)


