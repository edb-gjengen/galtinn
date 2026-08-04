from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
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

    def search(self, queryset: QuerySet, query: str) -> QuerySet:
        """Require every word of the query to match one of the search lookups,
        so e.g. "First Last" also finds "First Middle Last"."""
        for term in query.split():
            term_match = Q()
            for lookup in self.search_lookups:
                term_match |= Q(**{lookup: term})
            queryset = queryset.filter(term_match)
        return queryset

    def hook_queryset(self, queryset: QuerySet) -> QuerySet:
        queryset = queryset.annotate(full_name=Concat("first_name", Value(" "), "last_name"))

        query = " ".join(getattr(self, "query", "").split())
        if not query:
            return queryset.annotate(sort_priority=Value(0, output_field=IntegerField()))

        # Rank exact matches above prefix matches, prefix matches above
        # word-prefix matches, and anything else (substring hits) last.
        word_prefix_match = Q()
        for term in query.split():
            word_prefix_match &= (
                Q(first_name__istartswith=term)
                | Q(last_name__istartswith=term)
                | Q(username__istartswith=term)
                | Q(full_name__icontains=f" {term}")
            )
        return queryset.annotate(
            sort_priority=Case(
                When(Q(full_name__iexact=query) | Q(username__iexact=query), then=Value(0)),
                When(Q(full_name__istartswith=query) | Q(username__istartswith=query), then=Value(1)),
                When(word_prefix_match, then=Value(2)),
                default=Value(3),
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
