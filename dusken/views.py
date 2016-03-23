from braces.views import LoginRequiredMixin
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import FormView, DetailView
from dusken.forms import DuskenUserForm
from dusken.models import DuskenUser, MembershipType


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

        return super(IndexView, self).render_to_response(context, **response_kwargs)


class UserView(LoginRequiredMixin, DetailView):
    template_name = 'dusken/user_detail.html'

    def get_queryset(self):
        return DuskenUser.objects.filter(pk=self.kwargs['pk'])


class HomeView(UserView):
    template_name = 'dusken/home.html'

    def get_object(self, queryset=None):
        return self.request.user


class MembershipPurchase(FormView):
    template_name = 'dusken/membership_purchase.html'
    form_class = DuskenUserForm
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.objects.get(pk=settings.MEMBERSHIP_TYPE_ID)
        return super(MembershipPurchase, self).get_context_data(**kwargs)
