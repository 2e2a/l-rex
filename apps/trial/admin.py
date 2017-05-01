from django.contrib import admin

from . import models


admin.site.register(models.Trial)
admin.site.register(models.TrialList)
admin.site.register(models.UserTrial)
admin.site.register(models.UserTrialItem)
