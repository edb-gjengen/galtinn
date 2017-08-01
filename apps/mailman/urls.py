from django.conf.urls import url

from apps.mailman.views import MailmanMembership

urlpatterns = [
    url(r'^memberships/(?P<list_name>[0-9a-zA-Z_\-]+)/members/(?P<address>[0-9a-zA-Z@._\-]+)/$',
        MailmanMembership.as_view(),
        name='memberships'),
]
