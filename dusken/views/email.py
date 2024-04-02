from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from dusken.apps.mailman.api import get_lists_by_email


class EmailSubscriptions(LoginRequiredMixin, TemplateView):
    MAILMAN_LISTS = ["medlemmer"]  # TODO: Make these database objects
    template_name = "dusken/email_subscriptions.html"

    def get_context_data(self, **_kwargs):
        email = self.request.user.email

        # FIXME: Remove this context data from view and move to AJAX views
        return {
            **super().get_context_data(),
            "mailing_lists": self._get_mailinglists(email),
        }

    def _get_mailinglists(self, email):
        visible_lists = self.MAILMAN_LISTS
        if self.request.user.is_volunteer:
            visible_lists.append("aktive")  # FIXME: Hardcoded for now

        mailman_lists = get_lists_by_email(email)
        visible_lists_with_status = {}
        for mlist in visible_lists:
            visible_lists_with_status[mlist] = {
                "is_member": mlist in mailman_lists,
                "url": reverse("mailman:memberships", args=[mlist, email]),
            }

        return visible_lists_with_status
