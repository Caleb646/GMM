from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet

from . import constants as c


class MessageThreadFormSet(BaseModelFormSet):

    def clean(self):
        """
        Hook for doing any extra formset-wide cleaning after Form.clean() has
        been called on every form. Any ValidationError raised by this method
        will not be associated with a particular form; it will be accessible
        via formset.non_form_errors()
        """
        # Don't bother validating the formset unless each form is valid on its own
        if any(self.errors):       
            return
        for form in self.forms:
            job = form.cleaned_data.get('job_id') # an instance of the Job model
            accepted_answer = form.cleaned_data.get('accepted_answer')
            thread_type = form.cleaned_data.get('thread_type')
            thread_status = form.cleaned_data.get("thread_status")
            # if a thread is going to be closed then the above values have to be set correctly
            if thread_status == c.FIELD_VALUE_CLOSED_THREAD_STATUS:
                if job.name == c.FIELD_VALUE_UNKNOWN_JOB:
                    raise ValidationError(f"Job name cannot be {c.FIELD_VALUE_UNKNOWN_JOB} when closing a message.")
                if thread_type == c.FIELD_VALUE_UNKNOWN_THREAD_TYPE:
                    raise ValidationError(f"The thread type cannot be {c.FIELD_VALUE_UNKNOWN_THREAD_TYPE} when closing a message.")
                if not accepted_answer or accepted_answer == "":
                    raise ValidationError(f"The accepted answer has to be filled out when closing a message. If an accepted answer is not applicable type N/A in the field.")
