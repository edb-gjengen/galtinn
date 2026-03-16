from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dusken.api.serializers.users import DuskenUserSerializer
from dusken.models import DuskenUser


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class SessionLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(DuskenUserSerializer(user).data)


class SessionLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DuskenUserSerializer

    def get_object(self):
        return self.request.user


class SessionPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form = PasswordResetForm(data={"email": serializer.validated_data["email"]})
        if form.is_valid():
            form.save(request=request)
        # Always return 204 to prevent email enumeration
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionPasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = DuskenUser.objects.get(pk=uid)
        except DuskenUser.DoesNotExist, ValueError, OverflowError:
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        form = SetPasswordForm(
            user,
            data={
                "new_password1": serializer.validated_data["new_password"],
                "new_password2": serializer.validated_data["new_password"],
            },
        )
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        form.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": ["Incorrect password."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(status=status.HTTP_204_NO_CONTENT)
