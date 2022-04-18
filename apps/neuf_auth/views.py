from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from apps.neuf_auth.forms import NeufSetPasswordForm


class NeufPasswordChangeView(PasswordChangeView):
    form_class = NeufSetPasswordForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.user.log(message="Password changed", changed_by=self.request.user)

        messages.success(self.request, "{} 😎".format(_("Password changed")))
        return super().form_valid(form)


class NeufPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = NeufSetPasswordForm
    post_reset_login = True
    success_url = reverse_lazy("home")
    post_reset_login_backend = "django.contrib.auth.backends.ModelBackend"

    def form_valid(self, form):
        form.user.log(message="Password changed via password reset", changed_by=self.user)

        # Mark the e-mail as confirmed since the reset link is sent to the users current email
        form.user.confirm_email()

        messages.success(self.request, "{} 😎".format(_("Password changed")))
        return super().form_valid(form)
