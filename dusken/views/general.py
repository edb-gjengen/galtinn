from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import DetailView, FormView, TemplateView

from dusken.forms import DuskenAuthenticationForm, MembershipPurchaseForm, UserWidgetForm
from dusken.models import MembershipType, Order


class IndexView(FormView):
    form_class = DuskenAuthenticationForm
    template_name = "dusken/index.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        # Log in and redirect
        login(self.request, form.get_user())
        return redirect(settings.LOGIN_REDIRECT_URL)

    def render_to_response(self, context, **response_kwargs):
        # IF already logged in, then redirect
        if self.request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().render_to_response(context, **response_kwargs)


class HomeView(LoginRequiredMixin, DetailView):
    template_name = "dusken/home.html"

    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    membership_type = None

    def get_object(self, _queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        self.membership_type = MembershipType.get_default()
        self.membership_purchase_form = MembershipPurchaseForm(initial={"email": self.request.user.email})
        return super().get_context_data(**kwargs)


class HomeVolunteerView(LoginRequiredMixin, DetailView):
    template_name = "dusken/home_volunteer.html"

    def get_object(self, _queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_search"] = UserWidgetForm()
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    slug_field = "uuid"

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = "dusken/stats.html"

    def _parse_start_date(self):
        start_date = self.request.GET.get("start_date", None)
        if not start_date:
            return timezone.now().date().replace(month=8, day=1)

        return parse_date(start_date)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "start_date": self._parse_start_date()}
