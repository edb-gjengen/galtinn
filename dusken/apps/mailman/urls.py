from django.urls import re_path

from dusken.apps.mailman.views import MailmanMembership

app_name = "mailman"
urlpatterns = [
    re_path(
        r"^memberships/(?P<list_name>[\w_\-]+)/members/(?P<address>[^/]+)/$",
        MailmanMembership.as_view(),
        name="memberships",
    ),
]
