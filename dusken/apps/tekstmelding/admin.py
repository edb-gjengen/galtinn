from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dusken.apps.tekstmelding.models import (
    DeliveryReport,
    IncomingMessage,
    OutgoingMessage,
    OutgoingResponse,
    TekstmeldingEvent,
)


@admin.register(IncomingMessage)
class IncomingMessageAdmin(admin.ModelAdmin):
    search_fields = ["msisdn"]
    list_display = ["pk", "msgid", "msisdn", "msg", "timestamp"]
    list_filter = ["timestamp"]


@admin.register(OutgoingMessage)
class OutgoingMessageAdmin(admin.ModelAdmin):
    search_fields = ["msisdn", "content", "destination"]
    list_display = [
        "pk",
        "sender",
        "pricegroup",
        "content_type_id",
        "destination",
        "content",
        "timestamp",
        "show_incoming_link",
    ]
    list_filter = ["timestamp", "pricegroup", "content_type_id"]

    @admin.display(description=_("Incoming message"))
    def show_incoming_link(self, obj):
        if not obj.ext_id:
            return ""

        url = reverse("admin:tekstmelding_incomingmessage_change", args=[obj.ext_id])
        return format_html("<a href='{url}'>{incoming}</a>", url=url, incoming=obj.ext_id)


def _show_link(obj, model_name):
    if not obj:
        return ""

    url = reverse(f"admin:{model_name}_change", args=[obj.pk])
    return format_html("<a href='{url}'>{obj}</a>", url=url, obj=obj)


@admin.register(TekstmeldingEvent)
class TekstmeldingEventAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "action",
        "show_link_incoming",
        "show_link_outgoing",
        "show_link_dlr",
        "show_link_user",
        "timestamp",
    ]
    list_filter = ["timestamp", "action"]

    @admin.display(description=_("Incoming message"))
    def show_link_incoming(self, obj):
        return _show_link(obj.incoming, "tekstmelding_incomingmessage")

    @admin.display(description=_("Outgoing message"))
    def show_link_outgoing(self, obj):
        return _show_link(obj.outgoing, "tekstmelding_outgoingmessage")

    @admin.display(description=_("Delivery report"))
    def show_link_dlr(self, obj):
        return _show_link(obj.dlr, "tekstmelding_deliveryreport")

    @admin.display(description=_("Inside user"))
    def show_link_user(self, obj):
        return _show_link(obj.user, "inside_insideuser")


admin.site.register(DeliveryReport)
admin.site.register(OutgoingResponse)
