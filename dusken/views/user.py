from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, FormView

from dusken.forms import (UserEmailValidateForm, UserPhoneValidateForm, DuskenUserForm, 
                          DuskenUserUpdateForm, DuskenUserActivateForm)
from dusken.models import DuskenUser, Order
from dusken.utils import send_validation_sms, generate_username


class UserRegisterView(FormView):
    template_name = 'dusken/user_register.html'
    form_class = DuskenUserForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.username = generate_username(self.object.first_name, self.object.last_name)
        self.object.save()

        # Log the user in
        self.object.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, self.object)

        return redirect(self.get_success_url())


class UserActivateView(FormView):
    """ Registration via link sent by SMS. """
    template_name = 'dusken/user_activate.html'
    form_class = DuskenUserActivateForm
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        phone_number = kwargs.get('phone')
        code = kwargs.get('code')
        self.valid_link = False
        try:
            user = DuskenUser.objects.get(phone_number=phone_number)
        except DuskenUser.DoesNotExist:
            user = None
        if not user and len(code) == 8:
            self.valid_link = Order.objects.filter(phone_number=phone_number,
                                                   transaction_id__startswith=code).exists()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['valid_link'] = getattr(self, 'valid_link', False)
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['phone_number'] = '+' + self.kwargs.get('phone', '')
        initial['code'] = self.kwargs.get('code')
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.phone_number = self.get_initial().get('phone_number')
        self.object.username = generate_username(self.object.first_name, self.object.last_name)
        self.object.save()
        self.object.confirm_phone_number()

        # Log the user in
        self.object.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, self.object)

        return redirect(self.get_success_url())


class UserListView(LoginRequiredMixin, ListView):
    model = DuskenUser
    template_name = 'dusken/user_list.html'
    slug_field = 'uuid'


class UserDetailView(LoginRequiredMixin, DetailView):
    model = DuskenUser
    template_name = 'dusken/user_detail.html'
    slug_field = 'uuid'
    context_object_name = 'userobj'


class UserDetailMeView(UserDetailView):
    def get_object(self, queryset=None):
        return self.request.user


class UserUpdateView(LoginRequiredMixin, UpdateView):
    form_class = DuskenUserUpdateForm
    template_name = 'dusken/user_update.html'
    model = DuskenUser
    slug_field = 'uuid'
    context_object_name = 'userobj'


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


class UserPhoneValidateView(LoginRequiredMixin, TemplateView):
    form_class = UserPhoneValidateForm
    template_name = 'dusken/user_phone_confirm.html'
    success_url = reverse_lazy('user-phone-validate-success')

    def get(self, request, *args, **kwargs):
        user = request.user
        code_sent = False
        if user.phone_number and not user.phone_number_confirmed and not user.phone_number_key:
            send_validation_sms(user)
            code_sent = True
        context = {
            'form': self.form_class(),
            'user': user,
            'code_sent': code_sent
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)
        if form.is_valid():
            self.form_valid(request)
            return redirect(self.success_url)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

    def form_valid(self, request):
        request.user.confirm_phone_number()
        return redirect(self.success_url)


class UserPhoneValidateSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'dusken/user_phone_confirm_success.html'
