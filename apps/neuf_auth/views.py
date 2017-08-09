from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _

from apps.neuf_auth.forms import NeufSetPasswordForm
from dusken.models import UserLogMessage


class NeufPasswordChangeView(PasswordChangeView):
    form_class = NeufSetPasswordForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        UserLogMessage.objects.create(user=form.user, message='Password changed', changed_by=self.request.user)

        messages.success(self.request, '{} 😎'.format(_('Password changed')))
        return super().form_valid(form)


class NeufPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = NeufSetPasswordForm
    post_reset_login = True
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        UserLogMessage.objects.create(
            user=form.user, message='Password changed via password reset', changed_by=self.user)

        messages.success(self.request, '{} 😎'.format(_('Password changed')))
        return super().form_valid(form)
