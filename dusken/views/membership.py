import logging

from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from dusken.forms import MembershipPurchaseForm
from dusken.models import MembershipType, Membership

logger = logging.getLogger(__name__)


class MembershipListView(LoginRequiredMixin, ListView):
    model = Membership

    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).order_by('-start_date')

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.get_default()
        self.membership_purchase_form = MembershipPurchaseForm(initial={'email': self.request.user.email})
        return super().get_context_data(**kwargs)
