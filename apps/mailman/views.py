from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class MailmanMembership(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, list_name, address):
        # TODO: call mailman api
        print('in post')
        print(list_name, address)
        return Response()

    def delete(self, list_name, address):
        # TODO: call mailman api
        print('in delete')
        print(list_name, address)
        return Response(status=status.HTTP_204_NO_CONTENT)
