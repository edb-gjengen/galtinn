from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.views.generic import ListView, DetailView, UpdateView
from django.views.generic import TemplateView

from dusken.forms import UserEmailValidateForm
from dusken.models import DuskenUser


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
    fields = ['first_name', 'last_name', 'email', 'phone_number']


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
