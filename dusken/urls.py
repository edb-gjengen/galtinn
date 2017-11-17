from django.urls import re_path, include, path

from dusken.api import urls as api_urls
from dusken.views.email import EmailSubscriptions
from dusken.views.general import IndexView, HomeView, OrderDetailView, HomeVolunteerView, StatsView
from dusken.views.membership import MembershipListView
from dusken.views.orgunit import (OrgUnitListView, OrgUnitDetailView, OrgUnitEditView,
                                  OrgUnitEditUsersView)
from dusken.views.user import (UserRegisterView, UserActivateView,
                               UserDetailView, UserDetailMeView, UserListView,
                               UserUpdateView, UserUpdateMeView, UserSetUsernameView)
from dusken.views.validation import UserEmailValidateView, UserPhoneValidateView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('home/', HomeView.as_view(), name='home'),

    # User
    path('me/', UserDetailMeView.as_view(), name='user-detail-me'),
    path('me/update/', UserUpdateMeView.as_view(), name='user-update-me'),
    path('me/update/username/', UserSetUsernameView.as_view(), name='user-update-username'),
    re_path(r'^users/(?P<slug>[0-9a-z-]+)/$', UserDetailView.as_view(), name='user-detail'),
    re_path(r'^users/(?P<slug>[0-9a-z-]+)/update/$', UserUpdateView.as_view(), name='user-update'),
    path('users/', UserListView.as_view(), name='user-list'),

    # Registration
    path('register/', UserRegisterView.as_view(), name='user-register'),
    re_path(r'^activate/(?P<phone>[0-9]+)/(?P<code>[0-9a-zA-Z-]+)$', UserActivateView.as_view(), name='user-activate'),

    # Contact info validation
    re_path(r'^users/(?P<slug>[0-9a-z-]+)/validate_email/(?P<email_key>[0-9a-zA-Z-]+)$',
            UserEmailValidateView.as_view(),
            name='user-email-validate'),
    path('me/validate_phone/', UserPhoneValidateView.as_view(), name='user-phone-validate'),

    # Membership
    path('memberships/', MembershipListView.as_view(), name='membership-list'),

    re_path(r'^order/(?P<slug>[0-9a-z-]+)/$', OrderDetailView.as_view(), name='payment-detail'),

    # Volunteer
    path('volunteer/', HomeVolunteerView.as_view(), name='home-volunteer'),
    path('orgunits/', OrgUnitListView.as_view(), name='orgunit-list'),
    re_path(r'^orgunit/(?P<slug>[0-9a-z-]+)/$', OrgUnitDetailView.as_view(), name='orgunit-detail'),
    re_path(r'^orgunit/edit/(?P<slug>[0-9a-z-]+)/$', OrgUnitEditView.as_view(), name='orgunit-edit'),
    re_path(r'^orgunit/edit/users/(?P<slug>[0-9a-z-]+)/$', OrgUnitEditUsersView.as_view(), name='orgunit-edit-users'),
    re_path(r'^orgunits/(?P<slug>[0-9a-z-]+)/$', OrgUnitDetailView.as_view(), name='orgunit-detail'),

    # Email
    path('email/subscriptions/', EmailSubscriptions.as_view(), name='email-subscriptions'),

    # Stats
    path('stats/', StatsView.as_view(), name='stats'),
]

urlpatterns += [
    path('api/', include(api_urls)),
]
