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

    # FIXME: You are here
    def get_queryset(self):
        return super().get_queryset().order_by("-memberships__end_date")
