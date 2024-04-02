from django.db.models.signals import post_save
from django.dispatch import receiver

from dusken.models import DuskenUser
from dusken.utils import send_validation_email


@receiver(post_save, sender=DuskenUser)
def on_new_user_send_validation_email(_sender, instance=None, created=False, **_kwargs):
    if created:
        user = instance
        send_validation_email(user)
