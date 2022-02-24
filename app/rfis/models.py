import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from .managers import MyUserManager, MessageThreadManager, JobManager, MessageManager

class MyUser(AbstractUser):
    username = None
    email = models.EmailField('email address', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    def __str__(self):
        return self.email


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


class MessageThread(models.Model):
    gmail_thread_id = models.CharField(max_length=100)
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE)

    subject = models.CharField(max_length=400)
    class ThreadTypes(models.TextChoices):
        RFI = "RFI"

    thread_type = models.CharField(
        max_length=10,
        choices=ThreadTypes.choices,
        default=ThreadTypes.RFI,
    )

    due_date = models.DateTimeField()
    
    class ThreadStatus(models.TextChoices):
        OPEN = "OPEN"
        CLOSED = "CLOSED"

    thread_status = models.CharField(
        max_length=15,
        choices=ThreadStatus.choices,
        default=ThreadStatus.OPEN,
    )

    #if the person who started the thread is a Thomas Builders employee we can send them notifications
    message_thread_initiator = models.EmailField()

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
    message_id = models.CharField(max_length=100)
    message_thread_id = models.ForeignKey(MessageThread, on_delete=models.CASCADE)
    subject = models.CharField(max_length=400)
    body = models.TextField(default="")
    debug_unparsed_body = models.TextField(default="")
    fromm = models.EmailField()
    to = models.CharField(max_length=100)
    time_received = models.DateTimeField(default=timezone.now)

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
    filename = models.CharField(max_length=100)
    upload = models.FileField(upload_to="attachments", blank=True)

    def __str__(self):
        return self.filename


