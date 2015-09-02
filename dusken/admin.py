from django.contrib import admin
from dusken.models import Membership, OrgUnit, DuskenUser, MembershipType
from mptt.admin import MPTTModelAdmin


class OrgUnitAdmin(MPTTModelAdmin):
    filter_horizontal = ['groups']

admin.site.register(Membership)
admin.site.register(MembershipType)
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(DuskenUser)
