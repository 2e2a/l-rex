from django.contrib import admin

from . import models


@admin.register(models.Materials)
class MaterialsAdmin(admin.ModelAdmin):
    date_hierarchy = 'study__created_date'
    list_display = (
        'title',
        'study',
    )
    list_per_page = 32
    search_fields = (
        'title',
        'study__title',
    )
    readonly_fields = (
        'slug',
        'study',
    )
