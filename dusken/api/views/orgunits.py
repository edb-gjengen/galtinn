from django.http import JsonResponse, HttpResponseForbidden
from dusken.models import DuskenUser, OrgUnit


def remove_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_uuid = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    user = DuskenUser.objects.get(uuid=user_uuid)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)
    if request.user.has_group(orgunit.admin_group):
        if user.has_group(orgunit.group):
            orgunit.group.user_set.remove(user)
            if user.has_group(orgunit.admin_group):
                orgunit.admin_group.user_set.remove(user)
            success = True
        else:
            success = False
    else:
        success = False
    data = {
        'success': success
    }
    return JsonResponse(data)
