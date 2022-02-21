from django.http import HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext_lazy as _

from dusken.models import DuskenUser, OrgUnit


def remove_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_uuid = request.GET.get("user", None)
    orgunit_slug = request.GET.get("orgunit", None)
    member_type = request.GET.get("type", None)
    user = DuskenUser.objects.get(uuid=user_uuid)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)

    error = _("Error")
    if request.user.is_superuser or request.user.has_group(orgunit.admin_group):
        if member_type == "admin" and user.has_group(orgunit.admin_group):
            orgunit.remove_admin(user, request.user)
        elif user.has_group(orgunit.group):
            orgunit.remove_user(user, request.user)
        else:
            error = _("Can't remove user because the user is not in the group")
    else:
        error = _("You are not authorized to remove users")

    data = {"success": True, "error": error}
    return JsonResponse(data)


def add_user(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    user_id = request.GET.get("user", None)
    orgunit_slug = request.GET.get("orgunit", None)
    member_type = request.GET.get("type", None)
    if member_type == "admin_uuid":
        user = DuskenUser.objects.get(uuid=user_id)
        member_type = "admin"
    else:
        user = DuskenUser.objects.get(pk=user_id)
    orgunit = OrgUnit.objects.get(slug=orgunit_slug)
    success = False

    if orgunit.admin_group is None and not request.user.is_superuser:
        return JsonResponse({"success": False})

    error = _("Error")
    if request.user.is_superuser or request.user.has_group(orgunit.admin_group):
        if not user.has_group(orgunit.admin_group) and member_type == "admin":
            orgunit.add_admin(user, request.user)
            success = True
        elif not user.has_group(orgunit.group):
            orgunit.add_user(user, request.user)
            success = True
        else:
            error = _("User already added")
    else:
        error = _("You are not authorized to add users")

    data = {
        "success": success,
        "error": error,
    }
    return JsonResponse(data)
