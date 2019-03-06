from django.contrib import admin

from . import models


class QuestionnaireItemInline(admin.TabularInline):
    model = models.QuestionnaireItem


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
    inlines = [
        QuestionnaireItemInline,
    ]


@admin.register(models.QuestionnaireBlock)
class QuestionnaireBlockAdmin(admin.ModelAdmin):
    date_hierarchy = 'study__created_date'
    list_display = (
        'block',
        'study',
        'randomization'
    )
    list_per_page = 32
    search_fields = (
        'study__title',
    )


class RatingInline(admin.TabularInline):
    model = models.Rating
    readonly_fields = (
        'trial',
        'questionnaire_item',
        'question',
    )
    can_delete = False


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
    search_fields = (
        'questionnaire__study__title',
    )
    inlines = [
        RatingInline,
    ]

    def study(self, obj):
        return obj.questionnaire.study


@admin.register(models.Rating)
class RatingAdmin(admin.ModelAdmin):
    date_hierarchy = 'trial__questionnaire__study__created_date'
    list_display = (
        'pk',
        'study',
        'trial',
        'questionnaire_item',
        'question',
    )
    readonly_fields = (
        'trial',
        'questionnaire_item',
        'question',
    )
    list_per_page = 32
    search_fields = (
        'trial__questionnaire__study__title',
    )

    def questionnare(self, obj):
        return obj.trial.questionnaire

    def study(self, obj):
        return self.questionnare(obj).study
