import contextlib

from .base import *  # noqa: F403

ALLOWED_HOSTS = ["*"]
SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]

with contextlib.suppress(ImportError):
    from .local import *  # noqa: F403
