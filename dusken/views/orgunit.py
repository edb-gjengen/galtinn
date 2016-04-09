from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from dusken.models import OrgUnit


class OrgUnitListView(LoginRequiredMixin, ListView):
    model = OrgUnit
    template_name = 'dusken/orgunit_list.html'
    context_object_name = 'orgunits'


class OrgUnitDetailView(LoginRequiredMixin, DetailView):
    model = OrgUnit
    template_name = 'dusken/orgunit_detail.html'
    context_object_name = 'orgunit'

