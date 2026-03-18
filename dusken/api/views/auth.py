from django.contrib.auth.password_validation import password_validators_help_texts
from django.views.generic import TemplateView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class GenericOauth2Callback(TemplateView):
    template_name = "dusken/generic_oauth2_callback.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "code": self.request.GET.get("code"),
            "error": self.request.GET.get("error"),
            "error_description": self.request.GET.get("error_description"),
        }


class PasswordValidatorsView(APIView):
    permission_classes = [AllowAny]

    def get(self, _):
        return Response({"help_texts": password_validators_help_texts()})
