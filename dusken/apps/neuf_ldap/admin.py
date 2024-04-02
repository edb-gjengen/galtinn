from django.contrib import admin

from .models import LdapAutomountHome, LdapGroup, LdapUser


@admin.register(LdapGroup)
class LdapGroupAdmin(admin.ModelAdmin):
    exclude = ["dn", "usernames"]
    list_display = ["name", "gid"]
    search_fields = ["name"]


@admin.register(LdapUser)
class LdapUserAdmin(admin.ModelAdmin):
    exclude = ["dn", "password", "photo"]
    list_display = ["username", "first_name", "last_name", "email", "id"]
    search_fields = ["first_name", "last_name", "full_name", "username"]


@admin.register(LdapAutomountHome)
class LdapAutomountHomeAdmin(admin.ModelAdmin):
    search_fields = ["username"]
