from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView, UpdateView

from dusken.forms import OrgUnitEditForm, UserWidgetForm
from dusken.models import OrgUnit
from dusken.views.mixins import OrgUnitAdminRequiredMixin, VolunteerRequiredMixin


class OrgUnitListView(VolunteerRequiredMixin, ListView):
    template_name = "dusken/orgunit_list.html"
    context_object_name = "orgunits"
    queryset = OrgUnit.objects.filter(is_active=True)


class OrgUnitDetailView(VolunteerRequiredMixin, DetailView):
    model = OrgUnit
    template_name = "dusken/orgunit_detail.html"
    context_object_name = "orgunit"


class OrgUnitEditView(OrgUnitAdminRequiredMixin, UpdateView):
    model = OrgUnit
    form_class = OrgUnitEditForm
    template_name = "dusken/orgunit_edit.html"
    context_object_name = "orgunit"

    def get_success_url(self):
        slug = self.kwargs["slug"]
        return reverse("orgunit-detail", args=[slug])


class OrgUnitEditUsersView(OrgUnitAdminRequiredMixin, DetailView):
    model = OrgUnit
    template_name = "dusken/orgunit_edit_users.html"
    context_object_name = "orgunit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_search"] = UserWidgetForm
        context["members_config"] = {
            "membersUrl": reverse("orgunit-member-list", args=[self.object.slug]),
            "orgunitUrl": reverse("orgunit-detail", args=[self.object.slug]),
            "currentUserId": self.request.user.pk,
            "isSuperuser": self.request.user.is_superuser,
            "userUrl": reverse("user-detail", args=["__uuid__"]),
            "language": get_language(),
            "strings": {
                "lifelong": _("Lifelong"),
                "none": _("None"),
                "noMembers": _("No members"),
                "confirmDemote": _("Remove admin rights from {name}?"),
                "confirmDemoteSelf": _(
                    "You are about to remove your own admin rights, "
                    "and will no longer be able to manage this organisation. Continue?"
                ),
                "confirmRemove": _("Remove {name} from this organisation?"),
                "confirmRemoveSelf": _(
                    "You are about to remove yourself from this organisation, "
                    "and will no longer be able to manage it. Continue?"
                ),
                "networkError": _("Failed to contact server"),
            },
        }
        return context
