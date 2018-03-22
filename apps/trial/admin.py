from django.contrib import admin

from . import models


admin.site.register(models.Questionnaire)
admin.site.register(models.UserTrial)
admin.site.register(models.UserTrialItem)
