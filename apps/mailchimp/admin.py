from django.contrib import admin

from apps.mailchimp.models import MailChimpSubscription


class MailChimpSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "status"]
    list_filter = ["status"]
    search_fields = ["email"]


admin.site.register(MailChimpSubscription, MailChimpSubscriptionAdmin)
