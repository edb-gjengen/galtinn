from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.mailchimp.models import MailChimpSubscription

UserModel = get_user_model()


def _sync(user):
    subscriptions = MailChimpSubscription.objects.filter(email=user.email)
    for sub in subscriptions:
        sub.sync_to_mailchimp()


@receiver(pre_save, sender=UserModel)
def on_user_save_sync_to_mailchimp(sender, instance, raw, **kwargs):
    if raw:
        return
    # TODO: Sync in some cases
    # try:
    #     existing_user = UserModel.objects.get(pk=instance.pk)
    # except UserModel.DoesNotExist:
    #     existing_user = None
    #
    # _sync(instance)
