from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from dusken.forms import UserEmailValidateForm, UserPhoneValidateForm
from dusken.utils import send_validation_sms


class UserEmailValidateView(TemplateView):
    template_name = "dusken/user_email_confirm.html"
    success_url = reverse_lazy("home")

    def get(self, request, *args, **kwargs):
        form = UserEmailValidateForm(kwargs)
        if form.is_valid():
            return self.form_valid(form, request)

        context = {"errors": form.errors}
        return render(request, self.template_name, context)

    def form_valid(self, form, request):
        user = form.cleaned_data.get("user")
        user.confirm_email()
        messages.success(request, _("Success!"))

        return redirect(self.success_url)


class UserPhoneValidateView(LoginRequiredMixin, TemplateView):
    form_class = UserPhoneValidateForm
    template_name = "dusken/user_phone_confirm.html"
    success_url = reverse_lazy("home")

    def get(self, request, *args, **kwargs):
        user = request.user
        code_sent = False
        if user.phone_number and not user.phone_number_confirmed and not user.phone_number_key:
            send_validation_sms(user)
            code_sent = True
        context = {"form": self.form_class(), "user": user, "code_sent": code_sent}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)
        if form.is_valid():
            return self.form_valid(form, request)

        context = self.get_context_data()
        context["form"] = form
        return render(request, self.template_name, context)

    def form_valid(self, form, request):
        request.user.confirm_phone_number()
        messages.success(request, _("Success!"))

        return redirect(self.success_url)
