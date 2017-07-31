from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.common.mixins import BaseModel
from apps.mailchimp.tasks import update_list_subscription


class MailChimpSubscription(BaseModel):
    STATUS_SUBSCRIBED = 'subscribed'
    STATUS_PENDING = 'pending'
    STATUS_UNSUBSCRIBED = 'unsubscribed'
    STATUS_DEFAULT = STATUS_SUBSCRIBED

    STATUS_CHOICES = (
        (STATUS_SUBSCRIBED, _('subscribed')),
        (STATUS_PENDING, _('pending')),
        (STATUS_UNSUBSCRIBED, _('unsubscribed'))
    )

    email = models.EmailField(_("email"))
    status = models.CharField(
        _("status"), choices=STATUS_CHOICES, default=STATUS_DEFAULT, max_length=15)
    mailchimp_id = models.CharField(unique=True, max_length=50)

    def merge_field_data(self):
        # TODO: Add more?
        """
        Merge fields are configured per Mailchimp list using the create_merge_fields management command
        or the Mailchimp web ui.
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
        """ Sync all relevant data for MailChimpUser to Mailchimp """
        update_list_subscription.delay(email=self.email, status=self.status, merge_data=self.merge_field_data())

    def __str__(self):
        return '{} ({})'.format(self.email, self.status)

    class Meta:
        verbose_name = _('mailchimp user')
        verbose_name_plural = _('mailchimp users')
