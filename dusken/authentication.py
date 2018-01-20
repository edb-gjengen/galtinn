from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework.authentication import BasicAuthentication
from rest_framework.compat import authenticate

UserModel = get_user_model()


class UsernameModelBackend(ModelBackend):
    """ Lookup user on UserModel.username vs on UserModel.USERNAME_FIELD """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user


class UsernameBasicAuthentication(BasicAuthentication):
    def authenticate_credentials(self, userid, password, request=None):
        """
        Authenticate the userid and password against username and password
        with optional request for context.
        """
        credentials = {
            'username': userid,  # Note: Use 'username' keyword, overriding super class behaviour
            'password': password
        }
        user = authenticate(request=request, **credentials)

        if user is None:
            raise exceptions.AuthenticationFailed(_('Invalid username/password.'))

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (user, None)
