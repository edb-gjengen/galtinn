from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView

from dusken.models import OrgUnit


class OrgUnitListView(LoginRequiredMixin, ListView):
    model = OrgUnit
    template_name = 'dusken/orgunit_list.html'
    context_object_name = 'orgunits'
    queryset = OrgUnit.objects.filter(is_active=True)


class OrgUnitDetailView(LoginRequiredMixin, DetailView):
    model = OrgUnit
    template_name = 'dusken/orgunit_detail.html'
    context_object_name = 'orgunit'


class OrgUnitEditView(LoginRequiredMixin, UpdateView):
    model = OrgUnit
    template_name = 'dusken/orgunit_edit.html'
    context_object_name = 'orgunit'
    fields = ['name', 'short_name', 'email', 'phone_number', 'website', 'description']

    def get_success_url(self):
        slug = self.kwargs['slug']
        return reverse('orgunit-detail', args=[slug])
