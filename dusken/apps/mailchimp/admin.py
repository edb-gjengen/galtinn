from django.contrib import admin

from dusken.apps.mailchimp.models import MailChimpSubscription


@admin.register(MailChimpSubscription)
class MailChimpSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "status"]
    list_filter = ["status"]
    search_fields = ["email"]
