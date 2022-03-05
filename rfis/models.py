import datetime
from typing import Iterable, Optional
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

from .managers import MyUserManager, MessageThreadManager, JobManager, MessageManager
from . import constants as c, utils as u

class MyUser(AbstractUser):
    username = None
    email = models.EmailField('email address', unique=True)

    class UserType(models.TextChoices):
        EMPLOYEE = c.FIELD_VALUE_EMPLOYEE_USER_TYPE
        UNKNOWN = c.FIELD_VALUE_UNKNOWN_USER_TYPE

    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.UNKNOWN,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    def __str__(self):
        return self.email


class Dashboard(models.Model):
    slug = models.SlugField(unique=True)
    # on delete will set the owner to be the main admin specified in the .env file
    owner = models.ForeignKey(MyUser, on_delete=models.SET(u.get_main_admin_user)) #models.CharField(max_length=200)

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = str(uuid.uuid4())
        return super().save(*args, **kwargs)

class Job(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField()

    objects = JobManager()

    class Meta:
        ordering = ["start_date"]

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

#TODO add a time received field for message thread
class MessageThread(models.Model):
    gmail_thread_id = models.CharField(max_length=200)
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE)

    subject = models.CharField(max_length=400)
    class ThreadTypes(models.TextChoices):
        UNKNOWN = c.FIELD_VALUE_UNKNOWN_THREAD_TYPE
        RFI = c.FIELD_VALUE_RFI_THREAD_TYPE

    thread_type = models.CharField(
        max_length=10,
        choices=ThreadTypes.choices,
        default=ThreadTypes.UNKNOWN,
    )

    due_date = models.DateTimeField()
    
    class ThreadStatus(models.TextChoices):
        OPEN = c.FIELD_VALUE_OPEN_THREAD_STATUS
        CLOSED = c.FIELD_VALUE_CLOSED_THREAD_STATUS

    thread_status = models.CharField(
        max_length=15,
        choices=ThreadStatus.choices,
        default=ThreadStatus.OPEN,
    )

    #if the person who started the thread is a Thomas Builders employee we can send them notifications
    message_thread_initiator = models.ForeignKey(MyUser, on_delete=models.SET(u.get_main_admin_user)) #models.CharField(max_length=200)
    # blank=True has to be set or the field will be required in any model form
    accepted_answer = models.TextField(default="", blank=True) 

    objects = MessageThreadManager()

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now() + datetime.timedelta(days=7)
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return self.subject
class Message(models.Model):
    message_id = models.CharField(max_length=200)
    message_thread_id = models.ForeignKey(MessageThread, on_delete=models.CASCADE)
    subject = models.CharField(max_length=400)
    body = models.TextField(default="")
    debug_unparsed_body = models.TextField(default="")
    fromm = models.CharField(max_length=100)
    to = models.CharField(max_length=200)
    #TODO add Cc field
    time_received = models.DateTimeField()

    objects = MessageManager()

    class Meta:
        ordering = ["time_received"]

    def save(self, *args, **kwargs):
        if not self.time_received:
            self.time_received = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.subject


class Attachment(models.Model):
    message_id = models.ForeignKey(Message, on_delete=models.CASCADE)
    gmail_attachment_id = models.CharField(max_length=1000, default="Unknown")
    filename = models.CharField(max_length=100)
    time_received = models.DateTimeField()
    #upload = models.FileField(upload_to="attachments", blank=True)

    """
    I want to get the file data from Gmail, decode it, and pass it on to the browser
    for download without writing it to a file on the server. Use javascript to call a file download endpoint with
    the gmail attachment id and have that endpoint return this response

    https://docs.djangoproject.com/en/4.0/ref/request-response/#django.http.HttpResponse
    >>> response = HttpResponse(my_data, headers={
...     'Content-Type': 'application/vnd.ms-excel',
...     'Content-Disposition': 'attachment; filename="foo.xls"',
... })
    """
    class Meta:
        ordering = ["time_received"]

    def save(self, *args, **kwargs):
        if not self.time_received:
            self.time_received = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.filename


