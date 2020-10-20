from django.contrib import admin
from django.db.models import TextField

from apps.contrib.admin import MarkdownxAdminWidget
from . import models


class DemographicsAdminInline(admin.TabularInline):
    model = models.DemographicField

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Study)
class StudyAdmin(admin.ModelAdmin):
    search_fields = (
        'title',
    )
    date_hierarchy = 'created_date'
    list_display = (
        'title',
        'created_date',
        'is_published',
        'is_archived'
    )
    list_filter = (
        'is_published',
        'is_archived'
    )
    readonly_fields = (
        'slug',
    )
    autocomplete_fields = (
        'creator',
        'shared_with',
    )
    list_per_page = 32
    inlines = (
        DemographicsAdminInline,
    )
    formfield_overrides = {
        TextField: {'widget': MarkdownxAdminWidget},
    }


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
    readonly_fields = (
        'study',
    )
    search_fields = (
        'study__title',
    )
    inlines = [
        ScaleValueInline
    ]
