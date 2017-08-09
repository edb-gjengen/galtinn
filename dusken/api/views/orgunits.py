from django.http import JsonResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _

from dusken.models import DuskenUser, OrgUnit


def remove_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_uuid = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    user = DuskenUser.objects.get(uuid=user_uuid)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)

    if not request.user.is_superuser and orgunit.admin_group is not None and not request.user.has_group(orgunit.admin_group):
        return JsonResponse({'success': False})

    if user.has_group(orgunit.group):
        orgunit.remove_user(user, request.user)

    return JsonResponse(data={'success': True})


def add_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_pk = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    member_type = request.GET.get('type', None)
    user = DuskenUser.objects.get(pk=user_pk)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)
    success = False

    if orgunit.admin_group is None and not request.user.is_superuser:
        return JsonResponse({'success': False})

    if request.user.is_superuser or request.user.has_group(orgunit.admin_group):
        if not user.has_group(orgunit.admin_group) and member_type == 'admin':
            orgunit.add_admin(user, request.user)
            success = True
        elif not user.has_group(orgunit.group):
            orgunit.add_user(user, request.user)
            success = True

    data = {
        'success': success,
        'user_uuid': user.uuid,
        'user_name': user.get_full_name(),
        'user_email': user.email,
        'remove': _('Remove'),
        'admin': _('Admin')
    }
    return JsonResponse(data)
