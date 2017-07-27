from django.contrib import admin

from apps.neuf_auth.models import AuthProfile


class AuthProfileAdmin(admin.ModelAdmin):
    list_display = ['pk', 'user']


admin.site.register(AuthProfile, AuthProfileAdmin)
