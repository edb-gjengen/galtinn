from django_tomselect.autocompletes import AutocompleteModelView

from dusken.models import DuskenUser


class UserAutocompleteView(AutocompleteModelView):
    model = DuskenUser
    search_lookups = [
        "first_name__icontains",
        "last_name__icontains",
        "username__icontains",
    ]
    value_fields = ["id", "first_name", "last_name", "username"]
    virtual_fields = ["display_label"]
    ordering = ["-memberships__end_date"]
    page_size = 10

    def hook_prepare_results(self, results):
        """Customize the prepared results before sending to the client."""
        for result in results:
            full_name = f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
            result["display_label"] = f"{full_name} ({result.get('username', '')})"
        return results
