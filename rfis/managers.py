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

    def get_or_create(self, **kwargs):
        if self.filter(email=kwargs.get("email")).exists():
            return (self.get(email=kwargs.get("email")), False)
        # if password isnt present set it to a random one
        kwargs.setdefault("password", str(uuid.uuid4()))
        return (self.create_user(**kwargs), True)

    def reset_password(self, password):
        self.set_password(password)
        self.save()


class JobManager(BaseUserManager):

    def get_or_unknown(self, **kwargs):
        name = kwargs.get("name")   
        if self.all().filter(name=name).exists():
            return self.get(name=name)
        return self.get(name=c.FIELD_VALUE_UNKNOWN_JOB)   

    def get_or_create(self, **kwargs):
        if self.filter(name=kwargs.get("name")).exists():
            return (self.get(name=kwargs.get("name")), False)
        return (self.create(**kwargs), True)    

        
class MessageThreadManager(BaseUserManager):

    def get_or_create(self, **kwargs):
        gmail_thread_id = kwargs.get("gmail_thread_id")       
        if self.all().filter(gmail_thread_id=gmail_thread_id).exists():
            return (self.get(gmail_thread_id=gmail_thread_id), False)
        return (self.create(**kwargs), True)
        

class MessageManager(BaseUserManager):

    def get_or_create(self, **kwargs):       
        message_id = kwargs.get("message_id")
        if self.all().filter(message_id=message_id).exists():
            return (self.get(message_id=message_id), False)
        return (self.create(**kwargs), True)


