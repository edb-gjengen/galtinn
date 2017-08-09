from django.contrib.auth.models import Group
from django.http import JsonResponse, HttpResponseForbidden
from dusken.models import DuskenUser, OrgUnit, GroupProfile
from django.utils.translation import ugettext as _

def remove_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_uuid = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    user = DuskenUser.objects.get(uuid=user_uuid)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)
    if request.user.has_group(orgunit.admin_group) or request.user.is_superuser:
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


def add_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_pk = request.GET.get('user', None)
    orgunit_slug = request.GET.get('orgunit', None)
    member_type = request.GET.get('type', None)
    user = DuskenUser.objects.get(pk=user_pk)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)
    success = False
    if request.user.has_group(orgunit.admin_group) or request.user.is_superuser:
        if not user.has_group(orgunit.group):
            orgunit.group.user_set.add(user)
            success = True
        if not user.has_group(orgunit.admin_group) and member_type == 'admin':
            orgunit.admin_group.user_set.add(user)
            success = True
    if success:
        Group.objects.filter(profile__type=GroupProfile.TYPE_VOLUNTEERS).first().user_set.add(user)
    data = {
        'success': success,
        'user_uuid': user.uuid,
        'user_name': user.get_full_name(),
        'user_email': user.email,
        'remove': _('Remove'),
        'admin': _('Admin')
    }
    return JsonResponse(data)
