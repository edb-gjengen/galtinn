from typing import Any

from strawberry import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        return info.context.request.user.is_authenticated
