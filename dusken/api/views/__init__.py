import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler

from dusken.utils import send_validation_email

logger = logging.getLogger(__name__)


class ResendValidationEmailView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        send_validation_email(request.user)
        return Response({"response": "success"})


def api_500_handler(exception, context):
    response = drf_exception_handler(exception, context)
    if response is not None:
        return response

    logger.exception(exception)
    msg = "Galtinn is having issues, sorry about that :-/ Please try again later..."
    return Response({"detail": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
