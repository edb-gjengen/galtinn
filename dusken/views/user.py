from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, FormView
from django.contrib.auth import login
from django.http import HttpResponseRedirect

from dusken.forms import UserEmailValidateForm, DuskenUserForm
from dusken.models import DuskenUser


class UserRegisterView(FormView):
    template_name = 'dusken/user_register.html'
    form_class = DuskenUserForm
    success_url = '/home'

    def form_valid(self, form):
        # FIXME: better way?
        self.object = form.save()
        self.object.backend = 'django.contrib.auth.backends.ModelBackend'  # FIXME: Ninja!
        login(self.request, self.object)
        return HttpResponseRedirect(self.get_success_url())


class UserListView(LoginRequiredMixin, ListView):
    model = DuskenUser
    template_name = 'dusken/user_list.html'
    slug_field = 'uuid'


class UserDetailView(LoginRequiredMixin, DetailView):
    model = DuskenUser
    template_name = 'dusken/user_detail.html'
    slug_field = 'uuid'


class UserDetailMeView(UserDetailView):
    def get_object(self, queryset=None):
        return self.request.user


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = DuskenUser
    template_name = 'dusken/user_update.html'
    fields = ['first_name', 'last_name', 'date_of_birth', 'email', 'phone_number', 'place_of_study', 'street_address',
              'street_address_two', 'postal_code', 'city', 'country']


class UserUpdateMeView(UserUpdateView):
    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('user-detail-me')


class UserEmailValidateView(TemplateView):
    template_name = 'dusken/user_email_confirm.html'
    success_url = reverse_lazy('user-email-validate-success')

    def get(self, request, *args, **kwargs):
        form = UserEmailValidateForm(kwargs)
        if form.is_valid():
            self.form_valid(form)
            return redirect(self.success_url)

        context = {
            'errors': form.errors
        }
        return render(request, self.template_name, context)

    def form_valid(self, form):
        user = form.cleaned_data.get('user')
        user.confirm_email()


class UserEmailValidateSuccessView(TemplateView):
    template_name = 'dusken/user_email_confirm_success.html'


class MyPasswordChangeView(PasswordChangeView):
    form_class = SetPasswordForm
