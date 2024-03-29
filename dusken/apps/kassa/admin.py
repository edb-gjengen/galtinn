from django.contrib import admin

from dusken.apps.kassa.models import KassaEvent


@admin.register(KassaEvent)
class KassaEventAdmin(admin.ModelAdmin):
    list_display = ["id", "event", "card_number", "user_phone_number", "user_inside_id", "created"]
    list_filter = ["event"]
    search_fields = ["card_number", "user_phone_number", "user_inside_id"]


