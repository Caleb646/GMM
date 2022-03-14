import datetime
import json
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from . import constants as c
from .managers import JobManager, MessageManager, MessageThreadManager, MyUserManager


class GmailCredentials(models.Model):

    credentials = models.JSONField(null=True, default=None)

    class Meta:
        verbose_name_plural = "Gmail Credentials"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if credentials := cls.objects.filter(pk=1):
            return credentials.first()
        return cls.objects.create(pk=1, credentials=None)

    @classmethod
    def load_credentials(cls):
        credentials = cls.load()
        assert credentials, "Credentials cannot be None"
        assert credentials.credentials, "Gmail credentials cannot be None"
        return json.loads(credentials.credentials)


class MyUser(AbstractUser):
    username = None
    email = models.EmailField("email address", unique=True)
    can_notify = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    @staticmethod
    def get_user_sentinel_id():
        fullname, email = settings.ADMINS[0]  # just pick the first admin
        return MyUser.objects.get(email=email)

    def __str__(self):
        return self.email


class MessageLog(models.Model):
    slug = models.SlugField(unique=True)
    # on delete will set the owner to be the main admin specified in the .env file
    owner = models.ForeignKey(
        MyUser, on_delete=models.SET(MyUser.get_user_sentinel_id)
    )  # models.CharField(max_length=200)

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = str(uuid.uuid4())
        return super().save(*args, **kwargs)


class Job(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_date = models.DateTimeField()

    objects = JobManager()

    class Meta:
        ordering = ["start_date"]

    @staticmethod
    def get_job_sentinel_id():
        return Job.objects.get(name=c.FIELD_VALUE_UNKNOWN_JOB)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ThreadType(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_message_type_sentinel_id():  # returns the Unknown Message Type
        return ThreadType.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE)


class ThreadTypeAltName(models.Model):
    name = models.CharField(max_length=200, unique=True)
    thread_type = models.ForeignKey(
        ThreadType, on_delete=models.CASCADE, related_name="thread_type"
    )

    def __str__(self):
        return self.name


class Thread(models.Model):
    gmail_thread_id = models.CharField(max_length=200, unique=True)
    job_id = models.ForeignKey(Job, on_delete=models.SET(Job.get_job_sentinel_id))

    subject = models.CharField(max_length=400)

    thread_type = models.ForeignKey(
        ThreadType,
        default=ThreadType.get_message_type_sentinel_id,
        on_delete=models.SET(ThreadType.get_message_type_sentinel_id),
    )

    time_received = models.DateTimeField()
    due_date = models.DateTimeField()

    class ThreadStatus(models.TextChoices):
        OPEN = c.FIELD_VALUE_OPEN_THREAD_STATUS
        CLOSED = c.FIELD_VALUE_CLOSED_THREAD_STATUS

    thread_status = models.CharField(
        max_length=15,
        choices=ThreadStatus.choices,
        default=ThreadStatus.OPEN,
    )

    # if the person who started the thread is a Thomas Builders employee we can send them notifications
    message_thread_initiator = models.ForeignKey(
        MyUser, on_delete=models.SET(MyUser.get_user_sentinel_id)
    )  # models.CharField(max_length=200)
    # If a user is deleted by accident the message_thread_initiator will be set to the first admin user.
    # To know who was the original owner of the thread save it here
    original_initiator = models.CharField(max_length=300)
    # blank=True has to be set or the field will be required in any model form
    accepted_answer = models.TextField(default="", blank=True)

    objects = MessageThreadManager()

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now() + datetime.timedelta(days=7)
        if not self.time_received:
            self.time_received = timezone.now()
        if not self.original_initiator:
            self.original_initiator = self.message_thread_initiator.email
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return self.subject


class Message(models.Model):
    message_id = models.CharField(max_length=200, unique=True)
    message_thread_id = models.ForeignKey(Thread, on_delete=models.CASCADE)
    subject = models.CharField(max_length=400)
    body = models.TextField(default="")
    debug_unparsed_body = models.TextField(default="")
    fromm = models.CharField(max_length=100)
    to = models.CharField(max_length=200)
    cc = models.CharField(max_length=1000)
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
    # upload = models.FileField(upload_to="attachments", blank=True)

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
