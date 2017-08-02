from celery import shared_task

from apps.mailman.api import subscribe as subscribe_sync, unsubscribe as unsubscribe_sync


@shared_task
def subscribe(list_name, email, full_name, digest=False):
    subscribe_sync(list_name, email, full_name, digest=digest)


@shared_task
def unsubscribe(list_name, email):
    unsubscribe_sync(list_name, email)
