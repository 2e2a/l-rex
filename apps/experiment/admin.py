from django.contrib import admin

from . import models


admin.site.register(models.Experiment)
admin.site.register(models.TextItem)
admin.site.register(models.BinaryResponse)
admin.site.register(models.List)
admin.site.register(models.ListItem)
