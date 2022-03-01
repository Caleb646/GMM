from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.forms import modelformset_factory
from django import forms

from .. import constants as c, models as m, utils as u, formsets as f_sets



class DashboardView(View):
    template_name = 'rfis/dashboard/detailed.html'

    def get(self, request, *args, **kwargs):
        dashboard = m.Dashboard.objects.get(slug=kwargs["slug"])
        if not dashboard:
            return HttpResponse("dasboard doesnt exist.")

        ThreadsFormset = modelformset_factory(
            m.MessageThread,
            formset=f_sets.MessageThreadFormSet,
            fields=("job_id", "subject", "accepted_answer", "thread_type", "thread_status"),
            widgets = {
                'accepted_answer': forms.Textarea(attrs={'rows':2, 'cols':35}),
                'subject': forms.Textarea(attrs={'rows':2, 'cols':35, 'readonly': 'readonly'}),
                },
            extra=0
        )
        formset = ThreadsFormset(queryset=m.MessageThread.objects.filter(
            thread_status=m.MessageThread.ThreadStatus.OPEN, 
            message_thread_initiator=dashboard.owner)
            )
        return render(request, self.template_name, {"formset" : formset})

    #TODO should create a ThreadsFormset class
    def post(self, request, *args, **kwargs):      
        ThreadsFormset = modelformset_factory(
            m.MessageThread,
            formset=f_sets.MessageThreadFormSet,
            fields=("job_id", "subject", "accepted_answer", "thread_type", "thread_status"),
            widgets = {
                'accepted_answer': forms.Textarea(attrs={'rows':2, 'cols':35}),
                'subject': forms.Textarea(attrs={'rows':2, 'cols':35, 'readonly': 'readonly'}),
                },
            extra=0
        )
        formset = ThreadsFormset(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
        return render(request, self.template_name, {"formset" : formset})




