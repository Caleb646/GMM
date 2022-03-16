import random
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone

from ... import constants as c
from ... import models as m

PASSWORD = "1234"


def return_random_model_instance(model):
    return random.choice(list(model.objects.all()))


def create_dashboards():
    users = get_user_model().objects.all()
    ret = []
    for u in users:
        dashboard, created = m.MessageLog.objects.get_or_create(owner=u)
        ret.append(dashboard)
    return ret


def create_threads_w_n_max_messages(n):
    users = get_user_model().objects.all()
    ret = []
    num_msgs = random.randrange(0, n)

    thread_count = m.Thread.objects.all().count()
    if thread_count > 100:  # dont create more than 100 threads
        return []

    for u in users:
        job = return_random_model_instance(m.Job)
        thread_type = return_random_model_instance(m.ThreadType)

        thread, created = m.Thread.objects.get_or_create(
            gmail_thread_id=str(uuid.uuid4()),
            job_id=job,
            subject=str(uuid.uuid4()),
            thread_type=thread_type,
            time_received=timezone.now(),
            message_thread_initiator=u,
            accepted_answer=str(uuid.uuid4()),
        )
        ret.append(thread)
        for _ in range(num_msgs):
            message, mcreated = m.Message.objects.get_or_create(
                message_id=str(uuid.uuid4()),
                message_thread_id=thread,
                subject=str(uuid.uuid4()),
                body=str(uuid.uuid4()),
                to=str(uuid.uuid4()),
                fromm=str(uuid.uuid4()),
                cc=str(uuid.uuid4()),
            )

            m.Attachment.objects.get_or_create(
                message_id=message,
                gmail_attachment_id=str(uuid.uuid4()),
                filename=str(uuid.uuid4()),
            )
    return ret


def create_default_db_entries(nthreads=10):
    return {
        "users": {
            "1": get_user_model().objects.get_or_create(email="test1", password=PASSWORD),
            "2": get_user_model().objects.get_or_create(email="test2", password=PASSWORD),
            "3": get_user_model().objects.get_or_create(email="test3", password=PASSWORD),
            "4": get_user_model().objects.get_or_create(email="test4", password=PASSWORD),
            "4": get_user_model().objects.get_or_create(email="test5", password=PASSWORD),
            "staff": get_user_model().objects.get_or_create(
                email="staff", password=PASSWORD, is_staff=True
            ),
            "admin": get_user_model().objects.get_or_create(
                email="admin", password=PASSWORD, is_staff=True, is_superuser=True
            ),
        },
        "jobs": {
            c.FIELD_VALUE_UNKNOWN_JOB: m.Job.objects.get_or_create(
                name=c.FIELD_VALUE_UNKNOWN_JOB
            ),
            "Test Job": m.Job.objects.get_or_create(name="Test Job"),
        },
        "thread_types": {
            "1": m.ThreadType.objects.get_or_create(
                name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE
            ),
            "2": m.ThreadType.objects.get_or_create(name="RFI"),
        },
        "dashboards": create_dashboards(),  # list of dashboard objects
        "threads": create_threads_w_n_max_messages(nthreads),  # list of thread objects
    }
