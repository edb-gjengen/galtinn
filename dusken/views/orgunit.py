from django.urls import reverse
from django.views.generic import DetailView, ListView, UpdateView

from dusken.forms import OrgUnitEditForm, UserWidgetForm
from dusken.models import OrgUnit
from dusken.views.mixins import VolunteerRequiredMixin


class OrgUnitListView(VolunteerRequiredMixin, ListView):
    template_name = "dusken/orgunit_list.html"
    context_object_name = "orgunits"
    queryset = OrgUnit.objects.filter(is_active=True)


class OrgUnitDetailView(VolunteerRequiredMixin, DetailView):
    model = OrgUnit
    template_name = "dusken/orgunit_detail.html"
    context_object_name = "orgunit"


class OrgUnitEditView(VolunteerRequiredMixin, UpdateView):
    model = OrgUnit
    form_class = OrgUnitEditForm
    template_name = "dusken/orgunit_edit.html"
    context_object_name = "orgunit"

    def get_success_url(self):
        slug = self.kwargs["slug"]
        return reverse("orgunit-detail", args=[slug])


class OrgUnitEditUsersView(VolunteerRequiredMixin, DetailView):
    model = OrgUnit
    template_name = "dusken/orgunit_edit_users.html"
    context_object_name = "orgunit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_search"] = UserWidgetForm
        return context
