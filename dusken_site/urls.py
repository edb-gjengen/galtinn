from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dusken.views.home', name='home'),
    # url(r'^dusken/', include('dusken.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    
    # Django Rest Framework
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Django Rest Framework Swagger
    url(r'^api-docs/', include('rest_framework_swagger.urls')),

    # Dusken
    url(r'api/', include('dusken_api.urls')),
)
