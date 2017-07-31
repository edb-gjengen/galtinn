from celery import shared_task
from .api import update_list_subscription as update_list_subscription_sync


@shared_task
def update_list_subscription(email, status, merge_data=None, list_id=None):
    update_list_subscription_sync(email, status, merge_data=None, list_id=None)
