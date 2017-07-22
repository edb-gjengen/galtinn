from datetime import date

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib import admin
from django.db.models import Min
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin

from dusken.models import Membership, OrgUnit, DuskenUser, MembershipType, Order, MemberCard, PlaceOfStudy, \
    GroupProfile, UserLogMessage, OrgUnitLogMessage


class StartDateYearListFilter(admin.SimpleListFilter):
    title = _('year sold')
    parameter_name = 'start_date_year'

    def lookups(self, request, model_admin):
        Model = model_admin.model
        min_start_date = Model.objects.aggregate(Min('start_date'))
        min_year = 2005
        if min_start_date and min_start_date['start_date__min'] is not None:
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
    list_display = ['pk', 'show_user_link', 'membership_type', 'start_date', 'end_date', 'get_payment_type', 'created']
    list_filter = ['membership_type', 'order__payment_method', StartDateYearListFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'user__phone_number']
    readonly_fields = ['show_user_link']
    exclude = ['user']

    def get_payment_type(self, obj):
        if obj.order is None:
            return ''

        return obj.order.get_payment_method_display()

    get_payment_type.short_description = _('Payment method')
    get_payment_type.admin_order_field = 'payment__payment_method'

    def show_user_link(self, obj):
        if obj.user is None:
            return ''

        url = reverse("admin:dusken_duskenuser_change", args=[obj.user.pk])
        return format_html("<a href='{url}'>{user}</a>", url=url, user=obj.user)

    show_user_link.allow_tags = True
    show_user_link.short_description = _('User')


class OrgUnitAdmin(MPTTModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'contact_person', 'is_active']
    list_filter = ['is_active']
    readonly_fields = ['contact_person']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'product', 'show_user_link', 'phone_number', 'show_member_card_link',
                    'created', 'payment_method']
    list_filter = ['payment_method']
    search_fields = ['uuid', 'phone_number', 'member_card__card_number', 'user__username',
                     'user__first_name', 'user__last_name', 'user__email', 'user__phone_number']
    readonly_fields = ['uuid', 'product', 'price_nok', 'user', 'payment_method', 'transaction_id']

    def show_user_link(self, obj):
        if obj.user is None:
            return ''

        url = reverse("admin:dusken_duskenuser_change", args=[obj.user.pk])
        return format_html("<a href='{url}'>{user}</a>", url=url, user=obj.user)
    show_user_link.allow_tags = True
    show_user_link.short_description = _('User')

    def show_member_card_link(self, obj):
        if obj.member_card is None:
            return ''

        url = reverse("admin:dusken_membercard_change", args=[obj.member_card.pk])
        return format_html("<a href='{url}'>{card}</a>", url=url, card=obj.member_card)
    show_member_card_link.allow_tags = True
    show_member_card_link.short_description = _('Member card')


class DuskenUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = DuskenUser


class DuskenUserAdmin(UserAdmin):
    form = DuskenUserChangeForm

    _extra_fields = ('phone_number', 'date_of_birth', 'street_address', 'street_address_two', 'postal_code', 'city',
                     'country', 'place_of_study', 'legacy_id', 'uuid', 'stripe_customer_id')

    fieldsets = UserAdmin.fieldsets + (
            (_('Dusken fields'), {'fields': _extra_fields}),
    )

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.readonly_fields += ('uuid', 'legacy_id', 'stripe_customer_id')


class MemberCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'show_user_link', 'registered', 'created', 'is_active']
    list_filter = ['is_active', 'registered']
    search_fields = ['card_number', 'user__username', 'user__first_name', 'user__last_name', ]
    readonly_fields = ['card_number', 'show_user_link']
    exclude = ['user']

    def show_user_link(self, obj):
        if obj.user is None:
            return ''

        url = reverse("admin:dusken_duskenuser_change", args=[obj.user.pk])
        return format_html("<a href='{url}'>{user}</a>", url=url, user=obj.user)

    show_user_link.allow_tags = True
    show_user_link.short_description = _('User')


class UserLogMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'changed_by']
    search_fields = ['message']
    readonly_fields = ['user', 'message', 'changed_by']


class OrgUnitLogMessageAdmin(admin.ModelAdmin):
    list_display = ['org_unit', 'message', 'changed_by']
    search_fields = ['message']


class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ['pk', 'group', 'posix_name', 'description']


admin.site.register(DuskenUser, DuskenUserAdmin)
admin.site.register(GroupProfile, GroupProfileAdmin)
admin.site.register(MemberCard, MemberCardAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(MembershipType)
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(OrgUnitLogMessage, OrgUnitLogMessageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PlaceOfStudy)
admin.site.register(UserLogMessage, UserLogMessageAdmin)
