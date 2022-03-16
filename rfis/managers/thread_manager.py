from django.contrib.auth.base_user import BaseUserManager


class ThreadManager(BaseUserManager):
    def get_or_create(self, **kwargs):
        if thread := self.filter(gmail_thread_id=kwargs.get("gmail_thread_id")):
            return (thread.get(gmail_thread_id=kwargs.get("gmail_thread_id")), False)
        return (self.create(**kwargs), True)
