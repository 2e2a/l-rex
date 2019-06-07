from markdownx.admin import MarkdownxModelAdmin

from django.contrib import admin

from . import models


@admin.register(models.News)
class NewsAdmin(MarkdownxModelAdmin):
    date_hierarchy = 'date'
    readonly_fields = ('slug',)
    list_display = (
        'title',
        'date',
    )
    list_per_page = 32
