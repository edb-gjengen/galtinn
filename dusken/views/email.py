from django.views.generic import TemplateView

from apps.mailchimp.api import get_list_subscription
from apps.mailchimp.models import MailChimpSubscription
from apps.mailman.api import get_lists_by_email


class EmailSubscriptions(TemplateView):
    MAILMAN_LISTS = ['medlemmer', 'ninjatest']  # TODO: Make these database objects
    template_name = 'dusken/email_subscriptions.html'

    def get_context_data(self, **kwargs):
        email = self.request.user.email

        # FIXME: Remove this context data from view and move to AJAX views
        return {
            **super().get_context_data(),
            'newsletter_subscription': self._get_subscription(email),
            'mailing_lists': self._get_mailinglists(email)
        }

    def _get_mailinglists(self, email):
        visible_lists = self.MAILMAN_LISTS
        if self.request.user.is_volunteer:
            visible_lists.append('aktive')

        mailman_lists = get_lists_by_email(email)
        visible_lists_with_status = {}
        for mlist in visible_lists:
            visible_lists_with_status[mlist] = mlist in mailman_lists

        return visible_lists_with_status

    def _get_subscription(self, email):
        sub = MailChimpSubscription.objects.filter(email=email).first()
        if not sub:
            # If no local subscription, try fetching it
            sub = self._get_subscription_from_api(email)
        return sub

    def _get_subscription_from_api(self, email):
        api_sub = get_list_subscription(self.request.user.email)

        if api_sub is None:
            return

        return MailChimpSubscription.objects.create(email=email, status=api_sub['status'])
