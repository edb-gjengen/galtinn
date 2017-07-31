from django.contrib import admin

from apps.inside.models import InsideUser, InsideGroup, InsideCard


admin.site.register(InsideGroup)
admin.site.register(InsideUser)
admin.site.register(InsideCard)
