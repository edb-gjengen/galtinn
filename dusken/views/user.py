from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views.generic import ListView, DetailView, UpdateView

from dusken.models import DuskenUser


class UserListView(LoginRequiredMixin, ListView):
    model = DuskenUser
    template_name = 'dusken/user_list.html'
    slug_field = 'uuid'


class UserDetailView(LoginRequiredMixin, DetailView):
    model = DuskenUser
    template_name = 'dusken/user_detail.html'
    slug_field = 'uuid'


class UserDetailMeView(UserDetailView):
    def get_object(self, queryset=None):
        return self.request.user


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = DuskenUser
    template_name = 'dusken/user_update.html'
    fields = ['first_name', 'last_name', 'email', 'phone_number']


class UserUpdateMeView(UserUpdateView):
    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('user-detail-me')
