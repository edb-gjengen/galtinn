from __future__ import annotations

from typing import List, Optional

import strawberry.django
from strawberry import auto
from strawberry.types import Info  # noqa: TCH002

from dusken import models


@strawberry.django.type(models.MembershipType)
class MembershipType:
    id: auto
    slug: auto
    price: auto


@strawberry.type
class Query:
    @strawberry.field()
    def membership_types(self, _info: Info, is_default: Optional[bool] = None) -> List[MembershipType]:
        query = {} if is_default is None else {"is_default": is_default}
        # FIXME: How to allow using django types here?
        return models.MembershipType.objects.filter(**query)  # type: ignore

    # TODO: Add opening hours and other static app info from a separate app


schema = strawberry.Schema(query=Query)
