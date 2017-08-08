from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView

from dusken.models import OrgUnit
from dusken.views.mixins import VolunteerRequiredMixin


class OrgUnitListView(VolunteerRequiredMixin, ListView):
    template_name = 'dusken/orgunit_list.html'
    context_object_name = 'orgunits'
    queryset = OrgUnit.objects.filter(is_active=True)


class OrgUnitDetailView(VolunteerRequiredMixin, DetailView):
    model = OrgUnit
    template_name = 'dusken/orgunit_detail.html'
    context_object_name = 'orgunit'

    def get_context_data(self, **kwargs):
        admins = self.get_object().admin_group.user_set.order_by('first_name', 'last_name')
        return {
            **super().get_context_data(**kwargs),
            'admins': admins,
            'members': self.get_object().group.user_set.order_by('first_name', 'last_name').exclude(pk__in=admins),
        }


class OrgUnitEditView(VolunteerRequiredMixin, UpdateView):
    model = OrgUnit
    template_name = 'dusken/orgunit_edit.html'
    context_object_name = 'orgunit'
    fields = ['name', 'short_name', 'email', 'phone_number', 'website', 'description']

    def get_success_url(self):
        slug = self.kwargs['slug']
        return reverse('orgunit-detail', args=[slug])
