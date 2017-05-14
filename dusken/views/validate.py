from dusken.models import DuskenUser
from django.http import JsonResponse


def validate_email(request):
    data = {
        'is_taken': DuskenUser.objects.filter(email=request.GET.get('email', None)).exists()
    }
    return JsonResponse(data)
