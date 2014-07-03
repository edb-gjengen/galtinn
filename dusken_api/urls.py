from django.conf.urls import patterns, include, url
from dusken_api import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dusken.views.home', name='home'),
    # url(r'^dusken/', include('dusken.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    
    url(r'^members/$', views.MemberList.as_view()),
    url(r'^members/(?P<pk>[0-9]+)/$', views.MemberDetail.as_view()),

    url(r'^memberships/$', views.MembershipList.as_view()),
    url(r'^memberships/(?P<pk>[0-9]+)/$', views.MembershipDetail.as_view()),
)
