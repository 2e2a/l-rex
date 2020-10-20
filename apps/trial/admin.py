from django.db.models import TextField
from django.contrib import admin

from apps.contrib.admin import MarkdownxAdminWidget
from . import models


@admin.register(models.Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    date_hierarchy = 'study__created_date'
    list_display = (
        'number',
        'study',
    )
    list_per_page = 32
    search_fields = (
        'study__title',
    )
    fields = (
        'slug',
        'number',
        'study',
        'item_lists',
    )
    readonly_fields = fields
    ordering = (
        'study',
        'number',
    )


@admin.register(models.QuestionnaireBlock)
class QuestionnaireBlockAdmin(admin.ModelAdmin):
    date_hierarchy = 'study__created_date'
    list_display = (
        'block',
        'study',
        'randomization'
    )
    list_per_page = 32
    readonly_fields = (
        'study',
    )
    search_fields = (
        'study__title',
    )
    ordering = (
        'study',
        'block',
    )
    formfield_overrides = {
        TextField: {'widget': MarkdownxAdminWidget},
    }


class QuestionPropertyAdmin(admin.TabularInline):
    model = models.QuestionProperty
    fields = (
        'number',
        'scale_order',
    )
    readonly_fields = (
        'number',
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.QuestionnaireItem)
class QuestionnaireItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'questionnaire__study__created_date'
    list_display = (
        'number',
        'questionnaire',
        'study',
    )
    list_per_page = 32
    ordering = (
        'questionnaire__study',
        'questionnaire',
        'number'
    )
    search_fields = (
        'questionnaire__study__title',
    )
    fields = (
        'number',
        'questionnaire',
        'item_materials',
        'item',
        'question_order',
    )
    readonly_fields = (
        'number',
        'questionnaire',
        'item_materials',
        'item',
    )
    inlines = (
        QuestionPropertyAdmin,
    )

    def study(self, obj):
        return obj.questionnaire.study
    study.admin_order_field = 'questionnaire__study'

    def item_materials(self, obj):
        return obj.item.materials


class RatingInlineAdmin(admin.TabularInline):
    model = models.Rating
    fields = (
        'created',
        'scale_value',
        'trial',
        'questionnaire_item',
        'question',
        'comment',
    )
    ordering = (
        'created',
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DemographicsValueInlineAdmin(admin.TabularInline):
    model = models.DemographicValue

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Trial)
class TrialAdmin(admin.ModelAdmin):
    date_hierarchy = 'questionnaire__study__created_date'
    list_display = (
        'slug',
        'study',
        'questionnaire',
        'created',
    )
    list_per_page = 32
    ordering = (
        'questionnaire__study',
        'created',
    )
    fields = (
        'slug',
        'questionnaire',
        'created',
        'ended',
        'participant_id',
        'is_test',
    )
    readonly_fields = fields
    search_fields = (
        'questionnaire__study__title',
    )
    inlines = [
        RatingInlineAdmin,
        DemographicsValueInlineAdmin,
    ]

    def study(self, obj):
        return obj.questionnaire.study
    study.admin_order_field = 'questionnaire__study'
