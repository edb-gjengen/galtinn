from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from apps.tekstmelding.models import (
    DeliveryReport,
    IncomingMessage,
    OutgoingMessage,
    OutgoingResponse,
    TekstmeldingEvent,
)


class IncomingMessageAdmin(admin.ModelAdmin):
    search_fields = ["msisdn"]
    list_display = ["pk", "msgid", "msisdn", "msg", "timestamp"]
    list_filter = ["timestamp"]


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

    def show_incoming_link(self, obj):
        if not obj.ext_id:
            return ""

        url = reverse("admin:tekstmelding_incomingmessage_change", args=[obj.ext_id])
        return format_html("<a href='{url}'>{incoming}</a>", url=url, incoming=obj.ext_id)

    show_incoming_link.allow_tags = True
    show_incoming_link.short_description = _("Incoming message")


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

    def _show_link(self, obj, model_name):
        if not obj:
            return ""

        url = reverse("admin:{}_change".format(model_name), args=[obj.pk])
        return format_html("<a href='{url}'>{obj}</a>", url=url, obj=obj)

    def show_link_incoming(self, obj):
        return self._show_link(obj.incoming, "tekstmelding_incomingmessage")

    show_link_incoming.allow_tags = True
    show_link_incoming.short_description = _("Incoming message")

    def show_link_outgoing(self, obj):
        return self._show_link(obj.outgoing, "tekstmelding_outgoingmessage")

    show_link_outgoing.allow_tags = True
    show_link_outgoing.short_description = _("Outgoing message")

    def show_link_dlr(self, obj):
        return self._show_link(obj.dlr, "tekstmelding_deliveryreport")

    show_link_dlr.allow_tags = True
    show_link_dlr.short_description = _("Delivery report")

    def show_link_user(self, obj):
        return self._show_link(obj.user, "inside_insideuser")

    show_link_user.allow_tags = True
    show_link_user.short_description = _("Inside user")


admin.site.register(DeliveryReport)
admin.site.register(TekstmeldingEvent, TekstmeldingEventAdmin)
admin.site.register(IncomingMessage, IncomingMessageAdmin)
admin.site.register(OutgoingMessage, OutgoingMessageAdmin)
admin.site.register(OutgoingResponse)
