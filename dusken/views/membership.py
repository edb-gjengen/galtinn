import logging

from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import FormView, ListView

from dusken.forms import DuskenUserForm, MembershipRenewForm
from dusken.models import MembershipType, Membership

logger = logging.getLogger(__name__)


class MembershipPurchaseView(FormView):
    template_name = 'dusken/membership_purchase.html'
    form_class = DuskenUserForm
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.get_default()
        return super().get_context_data(**kwargs)


class MembershipRenewView(FormView):
    template_name = 'dusken/membership_renew.html'
    form_class = MembershipRenewForm

    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.get_default()
        return super().get_context_data(**kwargs)

    def get_initial(self):
        return {'email': self.request.user.email}


class MembershipListView(LoginRequiredMixin, ListView):
    model = Membership

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).order_by('-start_date')
