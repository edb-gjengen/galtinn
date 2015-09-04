from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic import FormView, DetailView
from dusken.models import DuskenUser


class HomeView(FormView):
    form_class = AuthenticationForm
    template_name = 'home.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        user = None  # TODO get from form
        login(self.request, user)

    def render_to_response(self, context, **response_kwargs):
        if self.request.user.is_authenticated():
            return redirect('profile')

        return super(HomeView, self).render_to_response(context, **response_kwargs)


class UserView(DetailView):
    template_name = 'profile.html'

    def get_queryset(self):
        return DuskenUser.objects.filter(pk=self.kwargs['pk'])


class ProfileView(UserView):
    template_name = 'profile.html'

    def get_object(self, queryset=None):
        print(self.request.user)
        return self.request.user
