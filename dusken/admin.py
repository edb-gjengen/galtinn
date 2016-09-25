from datetime import date

from django.conf import settings
from django.contrib import admin
from django.db.models import Min
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin

from dusken.models import Membership, OrgUnit, DuskenUser, MembershipType, Order, MemberCard


class StartDateYearListFilter(admin.SimpleListFilter):
    title = _('year sold')
    parameter_name = 'start_date_year'

    def lookups(self, request, model_admin):
        Model = model_admin.model
        min_start_date = Model.objects.aggregate(Min('start_date'))
        min_year = 0
        if min_start_date:
            min_year = min_start_date['start_date__min'].year
        years = range(min_year, timezone.now().year + 1)
        return zip(years, years)

    def queryset(self, request, queryset):
        # Compare the requested value to decide how to filter the queryset.
        year = self.value()
        if year is not None:
            year = int(year)
            return queryset.filter(start_date__gte=date(year, 1, 1), start_date__lte=date(year, 12, 31))


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['show_user_link', 'membership_type', 'start_date', 'end_date', 'get_payment_type', 'created']
    list_filter = ['membership_type', 'order__payment_method', StartDateYearListFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'user__phone_number']
    readonly_fields = ['show_user_link']
    exclude = ['user']

    def get_payment_type(self, obj):
        if obj.payment is None:
            return ''

        return obj.payment.get_payment_method_display()

    get_payment_type.short_description = _('Payment method')
    get_payment_type.admin_order_field = 'payment__payment_method'

    def show_user_link(self, obj):
        url = reverse("admin:dusken_duskenuser_change", args=[obj.user.pk])
        return format_html("<a href='{url}'>{user}</a>", url=url, user=obj.user)

    show_user_link.allow_tags = True
    show_user_link.short_description = _('User')


class OrgUnitAdmin(MPTTModelAdmin):
    filter_horizontal = ['groups', 'admin_groups']
    prepopulated_fields = {'slug': ('name',)}


class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ['uuid']


class DuskenUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'is_active',
                    'phone_number_validated']
    list_filter = ['is_active', 'phone_number_validated']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['uuid']


class MemberCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'show_user_link', 'registered_datetime', 'created', 'is_active']
    list_filter = ['is_active']
    search_fields = ['card_number']
    readonly_fields = ['card_number', 'show_user_link']
    exclude = ['user']

    def show_user_link(self, obj):
        url = reverse("admin:dusken_duskenuser_change", args=[obj.user.pk])
        return format_html("<a href='{url}'>{user}</a>", url=url, user=obj.user)

    show_user_link.allow_tags = True
    show_user_link.short_description = _('User')


admin.site.register(DuskenUser, DuskenUserAdmin)
admin.site.register(MemberCard, MemberCardAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(MembershipType)
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(Order, PaymentAdmin)

