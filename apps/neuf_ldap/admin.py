from django.contrib import admin
from .models import LdapGroup, LdapUser, LdapAutomountHome


class LdapGroupAdmin(admin.ModelAdmin):
    exclude = ['dn', 'usernames']
    list_display = ['name', 'gid']
    search_fields = ['name']


class LdapUserAdmin(admin.ModelAdmin):
    exclude = ['dn', 'password', 'photo']
    list_display = ['username', 'first_name', 'last_name', 'email', 'id']
    search_fields = ['first_name', 'last_name', 'full_name', 'username']


class LdapAutomountHomeAdmin(admin.ModelAdmin):
    search_fields = ['username']

admin.site.register(LdapGroup, LdapGroupAdmin)
admin.site.register(LdapUser, LdapUserAdmin)
admin.site.register(LdapAutomountHome, LdapAutomountHomeAdmin)
