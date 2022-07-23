from typing import List

import strawberry.django
from strawberry import auto

from dusken import models


@strawberry.django.type(models.MembershipType)
class MembershipType:
    id: auto
    slug: auto
    price: auto
    user: "User"


@strawberry.django.type(models.Membership)
class Membership:
    id: auto
    start_date: auto
    end_date: auto
    membership_type: MembershipType


@strawberry.django.type(models.PlaceOfStudy)
class PlaceOfStudy:
    id: auto
    name: auto
    short_name: auto


@strawberry.django.type(models.DuskenUser)
class User:
    id: auto
    first_name: auto
    last_name: auto
    username: auto
    email: auto
    date_of_birth: auto
    phone_number: str
    street_address: auto
    city: auto
    country: str
    place_of_study: PlaceOfStudy
    memberships: List[Membership]

    # is_volunteer: auto
