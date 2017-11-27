from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, UpdateView, FormView, DeleteView

from apps.neuf_auth.forms import SetUsernameForm
from dusken.forms import DuskenUserForm, DuskenUserUpdateForm, DuskenUserActivateForm, UserWidgetForm, UserDeleteForm
from dusken.models import DuskenUser, Order
from dusken.utils import generate_username
from dusken.views.mixins import VolunteerRequiredMixin


class UserRegisterView(FormView):
    template_name = 'dusken/user_register.html'
    form_class = DuskenUserForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.username = generate_username(self.object.first_name, self.object.last_name)
        self.object.set_password(form.cleaned_data['password'])
        self.object.save()
        self.object.set_ldap_hash(form.cleaned_data['password'])

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
        phone_number = '+' + kwargs.get('phone', '')
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
        self.object.set_password(form.cleaned_data['password'])
        self.object.save()
        self.object.set_ldap_hash(form.cleaned_data['password'])
        self.object.confirm_phone_number()

        # Log the user in
        self.object.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, self.object)
        return redirect(self.get_success_url())


class UserListView(VolunteerRequiredMixin, ListView):
    model = DuskenUser
    template_name = 'dusken/user_list.html'

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['user_search'] = UserWidgetForm
        return context


class UserDetailView(VolunteerRequiredMixin, DetailView):
    model = DuskenUser
    template_name = 'dusken/user_detail.html'
    slug_field = 'uuid'
    context_object_name = 'userobj'


class UserDetailMeView(LoginRequiredMixin, DetailView):
    model = DuskenUser
    template_name = 'dusken/user_detail.html'
    slug_field = 'uuid'
    context_object_name = 'userobj'

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


class UserSetUsernameView(LoginRequiredMixin, UpdateView):
    form_class = SetUsernameForm
    template_name = 'dusken/user_username.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.has_set_username:
                messages.error(self.request, _('Username can only be set once'))
                return redirect(self.success_url)

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        username = form.cleaned_data['username']
        self.object.log('Username set to {username}'.format(username=username))
        messages.success(self.request, '{} 😎'.format(_('Username set to {username}').format(username=username)))

        return redirect(self.success_url)


class UserDeleteView(LoginRequiredMixin, FormView):
    form_class = UserDeleteForm
    success_url = reverse_lazy('index')
    template_name = 'dusken/user_confirm_delete.html'

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'user': self.request.user,
        }

    def form_valid(self, form):
        user = str(self.request.user)
        self.request.user.delete()

        messages.success(
            self.request, _('So long {user} and good luck on your future travels 🚣'.format(user=user)))

        return super().form_valid(form)
