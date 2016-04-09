from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import FormView, DetailView

from dusken.models import Payment


class IndexView(FormView):
    form_class = AuthenticationForm
    template_name = 'dusken/index.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        # Log in and redirect
        login(self.request, form.get_user())
        return redirect(settings.LOGIN_REDIRECT_URL)

    def render_to_response(self, context, **response_kwargs):
        # IF already logged in, then redirect
        if self.request.user.is_authenticated():
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().render_to_response(context, **response_kwargs)


class HomeView(LoginRequiredMixin, DetailView):
    template_name = 'dusken/home.html'

    def get_object(self, queryset=None):
        return self.request.user


class HomeActiveView(LoginRequiredMixin, DetailView):
    template_name = 'dusken/home_active.html'

    def get_object(self, queryset=None):
        return self.request.user


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    slug_field = 'uuid'

    def get_queryset(self):
        return self.model.objects.filter(membership__user=self.request.user)
