from django.contrib import admin

from dusken.apps.neuf_auth.models import AuthProfile


class AuthProfileAdmin(admin.ModelAdmin):
    list_display = ["pk", "user"]
    readonly_fields = ["user"]


admin.site.register(AuthProfile, AuthProfileAdmin)
