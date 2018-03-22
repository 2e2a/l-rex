from django.contrib import admin

from . import models


admin.site.register(models.TextItem)
admin.site.register(models.List)
