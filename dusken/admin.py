from datetime import date

from django.conf import settings
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin

from dusken.models import Membership, OrgUnit, DuskenUser, MembershipType, Payment, MemberCard


class StartDateYearListFilter(admin.SimpleListFilter):
    title = _('year sold')
    parameter_name = 'start_date_year'

    YEARS = range(settings.INSIDE_START_YEAR, timezone.now().year + 1)

    def lookups(self, request, model_admin):
        return zip(self.YEARS, self.YEARS)

    def queryset(self, request, queryset):
        # Compare the requested value to decide how to filter the queryset.
        year = self.value()
        if year is not None:
            year = int(year)
            return queryset.filter(start_date__gte=date(year, 1, 1), start_date__lte=date(year, 12, 31))


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'membership_type', 'start_date', 'end_date', 'get_payment_type', 'created']
    list_filter = ['membership_type', 'payment__payment_method', StartDateYearListFilter]

    def get_payment_type(self, obj):
        if obj.payment is None:
            return ''

        return obj.payment.get_payment_method_display()

    get_payment_type.short_description = _('Payment method')
    get_payment_type.admin_order_field = 'payment__payment_method'


class OrgUnitAdmin(MPTTModelAdmin):
    filter_horizontal = ['groups']
    prepopulated_fields = {'slug': ('name',)}


class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ['uuid']


class DuskenUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'is_active',
                    'phone_number_validated']
    list_filter = ['is_active', 'phone_number_validated']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['uuid']


admin.site.register(DuskenUser, DuskenUserAdmin)


class MemberCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'registered_datetime', 'is_active', 'user']


admin.site.register(MemberCard, MemberCardAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(MembershipType)
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(Payment, PaymentAdmin)

