import csv
import io

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.utils import timezone

from dusken.models import DuskenUser

CMS_FIELDS = ["cms_id", "username", "email", "galtinn_id"]


@pytest.fixture
def kari(db):
    return DuskenUser.objects.create_user(
        "kari", email="kari@example.com", first_name="Kari", last_name="Nordmann", email_confirmed_at=timezone.now()
    )


@pytest.fixture
def ola(db):
    return DuskenUser.objects.create_user("ola", email="ola@example.com")


def match(tmp_path, *rows, **options):
    path = tmp_path / "cms.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CMS_FIELDS)
        writer.writeheader()
        writer.writerows({"galtinn_id": "", **row} for row in rows)
    out = io.StringIO()
    call_command("match_cms_users", str(path), stdout=out, **options)
    return list(csv.DictReader(io.StringIO(out.getvalue())))


def test_email_match_prefills_galtinn_id(tmp_path, kari):
    (row,) = match(tmp_path, {"cms_id": 1, "username": "kari-cms", "email": "KARI@example.com"})

    assert row["match"] == "email"
    assert row["galtinn_id"] == str(kari.pk)
    assert row["galtinn_username"] == "kari"
    assert row["galtinn_name"] == "Kari Nordmann"
    assert row["email_confirmed"] == "1"
    assert row["cms_id"] == "1"


def test_email_and_username_match(tmp_path, kari):
    (row,) = match(tmp_path, {"cms_id": 1, "username": "Kari", "email": "kari@example.com"})

    assert row["match"] == "email+username"
    assert row["galtinn_id"] == str(kari.pk)


def test_username_only_match_is_a_candidate_not_a_prefill(tmp_path, ola):
    (row,) = match(tmp_path, {"cms_id": 1, "username": "ola", "email": "other@example.com"})

    assert row["match"] == "username"
    assert row["galtinn_id"] == ""
    assert row["candidate_ids"] == str(ola.pk)
    assert row["email_confirmed"] == "0"


def test_email_and_username_pointing_at_different_users_is_a_conflict(tmp_path, kari, ola):
    (row,) = match(tmp_path, {"cms_id": 1, "username": "ola", "email": "kari@example.com"})

    assert row["match"] == "conflict"
    assert row["galtinn_id"] == ""
    assert row["candidate_ids"] == f"{kari.pk} {ola.pk}"
    assert row["galtinn_username"] == ""


@pytest.mark.django_db
def test_no_match_and_blank_email(tmp_path):
    (row,) = match(tmp_path, {"cms_id": 1, "username": "nobody", "email": ""})

    assert row["match"] == "none"
    assert row["galtinn_id"] == ""


def test_existing_link_is_kept(tmp_path, kari, ola):
    (row,) = match(tmp_path, {"cms_id": 1, "username": "ola", "email": "ola@example.com", "galtinn_id": kari.pk})

    assert row["match"] == "linked"
    assert row["galtinn_id"] == str(kari.pk)
    assert row["galtinn_username"] == "kari"


def test_group_option_adds_membership_column(tmp_path, kari, ola):
    kari.groups.add(Group.objects.create(name="Nettsidetilgang"))

    rows = match(
        tmp_path,
        {"cms_id": 1, "username": "kari", "email": "kari@example.com"},
        {"cms_id": 2, "username": "ola", "email": "ola@example.com"},
        group="Nettsidetilgang",
    )

    assert [row["in_group"] for row in rows] == ["1", "0"]
