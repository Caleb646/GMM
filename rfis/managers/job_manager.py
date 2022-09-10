from django.contrib.auth.base_user import BaseUserManager

from .. import constants as c


class JobManager(BaseUserManager):
    def get_or_unknown(self, **kwargs):
        if job := self.filter(name=kwargs.get("name")):
            # force queryset to be evaluated
            return job.get(name=kwargs.get("name"))
        return self.get(name=c.FIELD_VALUE_UNKNOWN_JOB)

    def get_or_create(self, **kwargs):
        if job := self.filter(name=kwargs.get("name")):
            return (job.get(name=kwargs.get("name")), False)
        return (self.create(**kwargs), True)
