from django.contrib import admin

from . import models


@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    readonly_fields = ('slug',)
    list_display = (
        'title',
        'date',
    )
    list_per_page = 32
