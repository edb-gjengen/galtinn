from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.common.mixins import BaseModel
from apps.mailchimp.tasks import update_list_subscription


class MailChimpSubscription(BaseModel):
    STATUS_SUBSCRIBED = 'subscribed'
    STATUS_PENDING = 'pending'
    STATUS_UNSUBSCRIBED = 'unsubscribed'
    STATUS_CLEANED = 'cleaned'
    STATUS_DEFAULT = STATUS_SUBSCRIBED

    STATUS_CHOICES = (
        (STATUS_SUBSCRIBED, _('subscribed')),
        (STATUS_PENDING, _('pending')),
        (STATUS_UNSUBSCRIBED, _('unsubscribed')),
        (STATUS_CLEANED, _('cleaned'))
    )

    email = models.EmailField(_("email"))
    status = models.CharField(
        _("status"), choices=STATUS_CHOICES, default=STATUS_DEFAULT, max_length=15)

    def merge_field_data(self):
        # TODO: Add more?
        """
        Merge fields are configured per Mailchimp list using the Mailchimp web UI.
        Each key in the returned dict should correspond to a merge field tag.
        """
        user = get_user_model().objects.filter(email=self.email).first()
        if user is None:
            return {}

        return {
            'FNAME': user.first_name,
            'LNAME': user.last_name
        }

    def sync_to_mailchimp(self):
        """ Sync all relevant data to Mailchimp """
        update_list_subscription.delay(email=self.email, status=self.status, merge_data=self.merge_field_data())

    @property
    def show_checked(self):
        return self.status == MailChimpSubscription.STATUS_SUBSCRIBED

    def __str__(self):
        return '{} ({})'.format(self.email, self.status)

    class Meta:
        verbose_name = _('mailchimp subscription')
        verbose_name_plural = _('mailchimp subscriptions')
