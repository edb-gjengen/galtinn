from django.http import JsonResponse, HttpResponseForbidden
from dusken.models import DuskenUser, OrgUnit


def remove_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_uuid = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    member_type = request.GET.get('type', None)
    user = DuskenUser.objects.get(uuid=user_uuid)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)

    if not request.user.is_superuser and orgunit.admin_group is not None and not request.user.has_group(orgunit.admin_group):
        return JsonResponse({'success': False})

    if member_type == 'admin' and user.has_group(orgunit.admin_group):
        orgunit.remove_admin(user, request.user)
    elif user.has_group(orgunit.group):
        orgunit.remove_user(user, request.user)

    data = {
        'success': True,
    }
    return JsonResponse(data)


def add_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_id = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    member_type = request.GET.get('type', None)
    if member_type == 'admin':
        user = DuskenUser.objects.get(uuid=user_id)
    else:
        user = DuskenUser.objects.get(pk=user_id)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)
    success = False

    if orgunit.admin_group is None and not request.user.is_superuser:
        return JsonResponse({'success': False})

    if request.user.is_superuser or request.user.has_group(orgunit.admin_group):
        if not user.has_group(orgunit.admin_group) and member_type == 'admin' or member_type == 'newadmin':
            orgunit.add_admin(user, request.user)
            success = True
        elif not user.has_group(orgunit.group):
            orgunit.add_user(user, request.user)
            success = True

    data = {
        'success': success,
    }
    return JsonResponse(data)
