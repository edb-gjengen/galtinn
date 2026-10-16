from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from dusken.forms import UserEmailValidateForm


class UserEmailValidateView(TemplateView):
    template_name = "dusken/user_email_confirm.html"
    success_url = reverse_lazy("home")

    def get(self, request, *_args, **kwargs):
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
