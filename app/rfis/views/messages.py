from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.shortcuts import get_object_or_404

from .. import constants as c, models as m, utils as u, formsets as f_sets



class DashboardView(View):
    template_name = 'rfis/dashboard/detailed.html'

    def get(self, request, *args, **kwargs):
        dashboard = get_object_or_404(m.Dashboard, slug=kwargs["slug"])
        formset = f_sets.MessageThreadFormSet(queryset=m.MessageThread.objects.filter(
            thread_status=m.MessageThread.ThreadStatus.OPEN, 
            message_thread_initiator=dashboard.owner)).create_model_formset()

        return render(request, self.template_name, {"formset" : formset})

    #TODO should create a ThreadsFormset class
    def post(self, request, *args, **kwargs):      
        formset = f_sets.MessageThreadFormSet().create_model_formset(request_post=request.POST, request_files=request.FILES)
        if formset.is_valid():
            formset.save()
        return render(request, self.template_name, {"formset" : formset})




