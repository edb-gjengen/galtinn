from django.contrib import admin
from dusken.models import Membership, OrgUnit, DuskenUser, MembershipType, Payment
from mptt.admin import MPTTModelAdmin


class OrgUnitAdmin(MPTTModelAdmin):
    filter_horizontal = ['groups']

admin.site.register(DuskenUser)
admin.site.register(Membership)
admin.site.register(MembershipType)
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(Payment)

