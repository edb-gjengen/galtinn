from django.views.generic import TemplateView

from apps.mailchimp.api import get_list_subscription
from apps.mailchimp.models import MailChimpSubscription


class EmailSubscriptions(TemplateView):
    template_name = 'dusken/email_subscriptions.html'

    def get_context_data(self, **kwargs):
        email = self.request.user.email
        sub = MailChimpSubscription.objects.filter(email=email).first()

        if not sub:
            # If no local subscription, try fetching it
            sub = self._get_subscription_from_api(email, sub)

        return {
            **super().get_context_data(),
            'newsletter_subscription': sub
        }

    def _get_subscription_from_api(self, email, sub):
        api_sub = get_list_subscription(self.request.user.email)

        if api_sub is None:
            return

        sub = MailChimpSubscription.objects.create(email=email, status=api_sub.status)

        return sub
