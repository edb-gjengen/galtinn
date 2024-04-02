# ruff: noqa: PTH118
import os
from pathlib import Path


class InvalidGitRepository(Exception):  # noqa: N818
    """Invalid git repository"""


def fetch_git_sha(path, head=None):  # noqa: C901
    """>>> fetch_git_sha(os.path.dirname(__file__))

    This is vendored from raven.fetch_git_sha
    """
    if not head:
        head_path = os.path.join(path, ".git", "HEAD")
        if not Path(head_path).exists():
            raise InvalidGitRepository(f"Cannot identify HEAD for git repository at {path}")

        with Path(head_path).open() as fp:
            head = str(fp.read()).strip()

        if head.startswith("ref: "):
            head = head[5:]
            revision_file = os.path.join(path, ".git", *head.split("/"))
        else:
            return head
    else:
        revision_file = os.path.join(path, ".git", "refs", "heads", head)

    if not Path(revision_file).exists():
        if not Path(os.path.join(path, ".git")).exists():
            raise InvalidGitRepository(f"{path} does not seem to be the root of a git repository")

        # Check for our .git/packed-refs' file since a `git gc` may have run
        # https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
        packed_file = os.path.join(path, ".git", "packed-refs")
        if Path(packed_file).exists():
            with Path(packed_file).open() as fh:
                for line in fh:
                    line = line.rstrip()  # noqa: PLW2901
                    if line and line[:1] not in ("#", "^"):
                        try:
                            revision, ref = line.split(" ", 1)
                        except ValueError:
                            continue
                        if ref == head:
                            return str(revision)

        raise InvalidGitRepository(f'Unable to find ref to head "{head}" in repository')

    with Path(revision_file).open() as fh:
        return str(fh.read()).strip()
