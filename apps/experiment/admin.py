from django.contrib import admin

from . import models


@admin.register(models.Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    date_hierarchy = 'study__created_date'
    list_display = (
        'title',
        'study',
    )
    list_per_page = 32
    search_fields = (
        'study__title',
    )
