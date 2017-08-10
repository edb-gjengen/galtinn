from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView

from dusken.models import OrgUnit
from dusken.views.mixins import VolunteerRequiredMixin
from dusken.forms import UserWidgetForm, OrgUnitEditForm


class OrgUnitListView(VolunteerRequiredMixin, ListView):
    template_name = 'dusken/orgunit_list.html'
    context_object_name = 'orgunits'
    queryset = OrgUnit.objects.filter(is_active=True)


class OrgUnitDetailView(VolunteerRequiredMixin, DetailView):
    model = OrgUnit
    template_name = 'dusken/orgunit_detail.html'
    context_object_name = 'orgunit'

    def get_context_data(self, **kwargs):
        if self.get_object().admin_group:
            admins = self.get_object().admin_group.user_set.order_by('first_name', 'last_name')
        else:
            admins = []

        if self.get_object().group:
            members = self.get_object().group.user_set.order_by('first_name', 'last_name').exclude(pk__in=admins)
        else:
            members = []

        return {
            **super().get_context_data(**kwargs),
            'admins': admins,
            'members': members,
        }


class OrgUnitEditView(VolunteerRequiredMixin, UpdateView):
    model = OrgUnit
    form_class = OrgUnitEditForm
    template_name = 'dusken/orgunit_edit.html'
    context_object_name = 'orgunit'

    def get_success_url(self):
        slug = self.kwargs['slug']
        return reverse('orgunit-detail', args=[slug])


class OrgUnitEditUsersView(VolunteerRequiredMixin, DetailView):
    model = OrgUnit
    template_name = 'dusken/orgunit_edit_users.html'
    context_object_name = 'orgunit'

    def get_context_data(self, **kwargs):
        context = super(OrgUnitEditUsersView, self).get_context_data(**kwargs)
        context['user_search'] = UserWidgetForm
        context['users_sorted'] = context['orgunit'].group.user_set.all().order_by('first_name', 'last_name', 'username')
        return context
