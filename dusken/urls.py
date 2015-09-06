from django.conf.urls import url, include
from dusken.api import urls as api_urls
from dusken.views import HomeView, ProfileView, UserView, MembershipPurchase

urlpatterns = [
    url(r'api/', include(api_urls)),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^me/$', ProfileView.as_view(), name='profile'),
    url(r'^user/(?P<pk>\d+)/$', UserView.as_view(), name='user-detail'),
    url(r'^membership/purchase/$', MembershipPurchase.as_view(), name='membership-purchase')
]
