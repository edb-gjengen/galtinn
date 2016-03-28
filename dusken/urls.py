from django.conf.urls import url, include
from dusken.api import urls as api_urls
from dusken.views import IndexView, HomeView, UserDetailView, MembershipPurchase, UserDetailMeView,\
    MembershipListView, MembershipActivateView, UserListView, UserUpdateView, UserUpdateMeView

urlpatterns = [
    url(r'api/', include(api_urls)),
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^home/$', HomeView.as_view(), name='home'),

    url(r'^user/(?P<slug>[0-9a-z-]+)/$', UserDetailView.as_view(), name='user-detail'),
    url(r'^me/$', UserDetailMeView.as_view(), name='user-detail-me'),
    url(r'^user/(?P<slug>[0-9a-z-]+)/update/$', UserUpdateView.as_view(), name='user-update'),
    url(r'^me/update/$', UserUpdateMeView.as_view(), name='user-update-me'),
    url(r'^users/$', UserListView.as_view(), name='user-list'),

    url(r'^memberships/$', MembershipListView.as_view(), name='membership-list'),
    url(r'^membership/purchase/$', MembershipPurchase.as_view(), name='membership-purchase'),
    url(r'^activate/$', MembershipActivateView.as_view(), name='membership-activate'),
]

