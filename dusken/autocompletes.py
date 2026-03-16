from django.db.models import QuerySet, Value
from django.db.models.functions import Concat
from django_tomselect.autocompletes import AutocompleteModelView

from dusken.models import DuskenUser


class UserAutocompleteView(AutocompleteModelView):
    model = DuskenUser
    search_lookups = [
        "first_name__icontains",
        "last_name__icontains",
        "username__icontains",
        "full_name__icontains",
    ]

    def hook_queryset(self, queryset: QuerySet) -> QuerySet:
        return queryset.annotate(
            full_name=Concat("first_name", Value(" "), "last_name")
        )

    value_fields = ["id", "first_name", "last_name", "username"]
    virtual_fields = ["display_label", "full_name"]
    ordering = ["first_name", "last_name", "-memberships__end_date"]
    page_size = 10

    def hook_prepare_results(self, results):
        """Customize the prepared results before sending to the client."""
        for result in results:
            full_name = f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
            result["full_name"] = full_name
            result["display_label"] = f"{full_name} ({result.get('username', '')})"
        return results
