from django.contrib import admin

from . import models


@admin.register(models.Study)
class StudyAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = (
        'title',
        'created_date',
        'status',
    )
    list_per_page = 32


class ScaleValueInline(admin.TabularInline):
    model = models.ScaleValue


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    date_hierarchy = 'study__created_date'
    list_display = (
        'number',
        'study',
        'question',
    )
    list_per_page = 32
    search_fields = (
        'study__title',
    )
    inlines = [
        ScaleValueInline
    ]
