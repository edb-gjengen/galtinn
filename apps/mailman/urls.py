from django.conf.urls import url

from apps.mailman.views import MailmanMembership

urlpatterns = [
    url(r'^memberships/(?P<list_name>[\w_\-]+)/members/(?P<address>[^/]+)/$',
        MailmanMembership.as_view(),
        name='memberships'),
]
