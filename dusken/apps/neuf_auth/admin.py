from django.contrib import admin

from dusken.apps.neuf_auth.models import AuthProfile


@admin.register(AuthProfile)
class AuthProfileAdmin(admin.ModelAdmin):
    list_display = ["pk", "user"]
    readonly_fields = ["user"]


