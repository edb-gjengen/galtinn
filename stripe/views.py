from django.shortcuts import render

# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response

from stripe.api import charge

@api_view(['POST'])
def charge(request):
    result = charge(request.POST)
    # TODO serialize result
    return Response(result)
