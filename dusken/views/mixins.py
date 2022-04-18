from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


class PermissionRequiredMessagesMixin(PermissionRequiredMixin):
    permission_denied_message = _("You do not have access to this page")

    def handle_no_permission(self):
        messages.error(self.request, self.get_permission_denied_message())
        return super().handle_no_permission()


class VolunteerRequiredMixin(PermissionRequiredMessagesMixin):
    permission_denied_message = _("You need to be a volunteer to see this page")
    login_url = reverse_lazy("home-volunteer")

    def has_permission(self):
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return True

        return user.is_authenticated and user.is_volunteer
