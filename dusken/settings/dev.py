import contextlib

from .base import *  # noqa: F403

ALLOWED_HOSTS = ["*"]

with contextlib.suppress(ImportError):
    from .local import *  # noqa: F403
