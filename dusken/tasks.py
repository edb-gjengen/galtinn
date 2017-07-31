from celery import shared_task
from django.core.mail import send_mail


@shared_task()
def send_mail_task(subject, from_mail, message, recipient_list, html_message=None):
    return send_mail(subject, message, from_mail, recipient_list, html_message=html_message)
