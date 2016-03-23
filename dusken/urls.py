from django.conf.urls import url, include
from dusken.api import urls as api_urls
from dusken.views import IndexView, HomeView, UserView, MembershipPurchase

urlpatterns = [
    url(r'api/', include(api_urls)),
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^home/$', HomeView.as_view(), name='home'),
    url(r'^user/(?P<pk>\d+)/$', UserView.as_view(), name='user-detail'),
    url(r'^membership/purchase/$', MembershipPurchase.as_view(), name='membership-purchase')
]
