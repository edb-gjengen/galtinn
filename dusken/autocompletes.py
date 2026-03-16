from django.db.models import Case, IntegerField, QuerySet, Value, When
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
        query = getattr(self, "query", "")
        return queryset.annotate(
            full_name=Concat("first_name", Value(" "), "last_name"),
            sort_priority=Case(
                When(first_name__istartswith=query, then=Value(0)),
                When(first_name__icontains=query, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        )

    value_fields = ["id", "first_name", "last_name", "username"]
    virtual_fields = ["display_label", "full_name"]
    ordering = ["sort_priority", "full_name", "-memberships__end_date"]
    page_size = 10

    def hook_prepare_results(self, results):
        """Customize the prepared results before sending to the client."""
        for result in results:
            full_name = f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
            result["full_name"] = full_name
            result["display_label"] = f"{full_name} ({result.get('username', '')})"
        return results
