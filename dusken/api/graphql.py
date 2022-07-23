from typing import List, Optional

import strawberry.django
from strawberry import auto
from strawberry.types import Info

from dusken import models


@strawberry.django.type(models.MembershipType)
class MembershipType:
    id: auto
    slug: auto
    price: auto


@strawberry.type
class Query:
    @strawberry.field()
    def membership_types(self, info: Info, is_default: Optional[bool] = None) -> List[MembershipType]:
        query = {} if is_default is None else {"is_default": is_default}
        return models.MembershipType.objects.filter(**query)

    # TODO: Add opening hours and other static app info from a separate app


schema = strawberry.Schema(query=Query)
