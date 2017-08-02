import logging

import requests

from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mailman.api import subscribe, unsubscribe

logger = logging.getLogger(__name__)


class MailmanMembership(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, list_name, address):
        full_name = self.request.query_params.get('full_name')
        if not full_name:
            full_name = self.request.user.get_full_name()

        try:
            ret = subscribe(list_name, address, full_name)
        except requests.exceptions.HTTPError as e:
            logger.info(e)
            msg = str(e)
            code = 'error'
            if e.response.status_code == status.HTTP_409_CONFLICT:
                msg = _('Email already subscribed')
                code = 'duplicate'

            raise ValidationError(msg, code=code)

        return Response(ret, status=status.HTTP_201_CREATED)

    def delete(self, request, list_name, address):
        try:
            unsubscribe(list_name, address)
        except requests.exceptions.HTTPError as e:
            logger.info(e)
            msg = str(e)
            code = 'error'
            if e.response.status_code == status.HTTP_404_NOT_FOUND:
                msg = _('Email {} not on list').format(address)
                code = 'not_found'

            raise ValidationError(msg, code=code)

        return Response(status=status.HTTP_204_NO_CONTENT)
