from django.conf.urls import url, include
from dusken.views import HomeView, ProfileView, UserView

urlpatterns = [
    url(r'api/', include('dusken.api.urls')),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^me/$', ProfileView.as_view(), name='profile'),
    url(r'^user/(?P<pk>\d+)/$', UserView.as_view(), name='user-detail')
]
