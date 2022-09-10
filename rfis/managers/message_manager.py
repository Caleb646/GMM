from django.contrib.auth.base_user import BaseUserManager


class MessageManager(BaseUserManager):
    def get_or_create(self, **kwargs):
        if message := self.filter(message_id=kwargs.get("message_id")):
            return (message.get(message_id=kwargs.get("message_id")), False)
        return (self.create(**kwargs), True)
