from django.contrib.auth.base_user import BaseUserManager

from .. import constants as c


class ThreadManager(BaseUserManager):

    def get_or_create(self, **kwargs):
        if thread := self.filter(gmail_thread_id=kwargs.get("gmail_thread_id")):
            return (thread.get(gmail_thread_id=kwargs.get("gmail_thread_id")), False)
        return (self.create(**kwargs), True)

    def open_messages(self, user):
        return self.filter(message_thread_initiator=user, thread_status=c.FIELD_VALUE_OPEN_THREAD_STATUS)
