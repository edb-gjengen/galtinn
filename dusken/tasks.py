from datetime import timedelta
from smtplib import SMTPException

from django.core.mail import send_mail
from django.core.management import call_command
from django.tasks import task


def retry_mail(exc, result):
    """Retry while the mail server is unreachable: 5, 10, 20, 40, 80 minutes, then every 2 hours."""
    if not isinstance(exc, (SMTPException, OSError)):
        return None
    return timedelta(minutes=min(5 * 2 ** (result.attempts - 1), 120))


# Ten attempts span about 11 hours. django-stubs does not know task() forwards these to django-ox yet.
@task(max_attempts=10, backoff=retry_mail)  # type: ignore[call-overload]
def send_mail_task(subject, from_mail, message, recipient_list, html_message=None):
    send_mail(subject, message, from_mail, recipient_list, html_message=html_message)


@task
def prune_tasks():
    call_command("ox_prune")
