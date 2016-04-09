from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, ListView

from dusken.forms import DuskenUserForm, MembershipActivateForm, MembershipRenewForm
from dusken.models import MembershipType, Membership


class MembershipPurchaseView(FormView):
    template_name = 'dusken/membership_purchase.html'
    form_class = DuskenUserForm
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.objects.get(pk=settings.MEMBERSHIP_TYPE_ID)
        return super().get_context_data(**kwargs)


class MembershipRenewView(FormView):
    template_name = 'dusken/membership_renew.html'
    form_class = MembershipRenewForm

    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.objects.get(pk=settings.MEMBERSHIP_TYPE_ID)
        return super().get_context_data(**kwargs)


class MembershipListView(LoginRequiredMixin, ListView):
    model = Membership

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.request.user.pk)


class MembershipActivateView(FormView):
    template_name = 'dusken/membership_activate.html'
    form_class = MembershipActivateForm

    def form_valid(self, form):
        print("YEY")
