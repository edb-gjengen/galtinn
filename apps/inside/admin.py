from django.contrib import admin

# Register your models here.
from apps.inside.models import InsideUser, InsideGroup, InsideCard


admin.site.register(InsideGroup)
admin.site.register(InsideUser)
admin.site.register(InsideCard)
