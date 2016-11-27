from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dusken.utils import send_validation_email


class ResendValidationEmailView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None):
        send_validation_email(request.user)
        return Response({'response': 'success'})
