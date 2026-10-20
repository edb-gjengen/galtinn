from datetime import timedelta
from smtplib import SMTPServerDisconnected
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django_ox.models import OxTask
from django_ox.testing import run_tasks

from dusken.tasks import prune_tasks, send_mail_task


def enqueue_mail():
    return send_mail_task.enqueue("Subject", "from@example.com", "Body", ["ola@example.com"])


class SendMailTaskTests(TestCase):
    def test_sends(self):
        enqueue_mail()
        assert mail.outbox == []

        run_tasks(raise_failures=True)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["ola@example.com"]

    def test_retries_while_mail_server_is_down(self):
        result = enqueue_mail()

        with patch("dusken.tasks.send_mail", side_effect=SMTPServerDisconnected):
            run_tasks()
        db_task = OxTask.objects.get(pk=result.id)
        assert db_task.status == "READY"
        assert db_task.attempts == 1
        assert db_task.max_attempts == 10
        assert timedelta(minutes=4) < db_task.run_after - timezone.now() <= timedelta(minutes=5)

        db_task.run_after = timezone.now()
        db_task.save()
        run_tasks(raise_failures=True)
        assert len(mail.outbox) == 1

    def test_does_not_retry_other_errors(self):
        result = enqueue_mail()

        with patch("dusken.tasks.send_mail", side_effect=ValueError):
            run_tasks()
        assert OxTask.objects.get(pk=result.id).status == "FAILED"


class PruneTasksTests(TestCase):
    def test_removes_old_finished_tasks(self):
        result = enqueue_mail()
        run_tasks(raise_failures=True)
        OxTask.objects.filter(pk=result.id).update(finished_at=timezone.now() - timedelta(days=8))

        prune_tasks.enqueue()
        run_tasks(raise_failures=True)
        assert not OxTask.objects.filter(pk=result.id).exists()
