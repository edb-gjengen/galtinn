from django.contrib import admin

from apps.mailchimp.models import MailChimpSubscription


class MailChimpSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'status', 'mailchimp_id']
    list_filter = ['status']
    search_fields = ['email', 'mailchimp_id']

admin.site.register(MailChimpSubscription, MailChimpSubscriptionAdmin)
