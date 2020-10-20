from django import forms
from django.contrib import admin
from django.db.models import TextField

from apps.contrib.admin import MarkdownxAdminWidget
from . import models


class ItemQuestionInlineAdmin(admin.TabularInline):
    model = models.ItemQuestion
    fields = (
        'number',
        'question',
        'scale_labels',
        'legend',
    )
    readonly_fields = (
        'number',
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class ItemFeedbackInlineAdmin(admin.TabularInline):
    model = models.ItemFeedback
    fields = (
        'item',
        'question',
        'scale_values',
        'feedback',
    )
    readonly_fields = (
        'item',
        'question',
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class ItemAdminMixin:
    date_hierarchy = 'materials__study__created_date'
    list_per_page = 32
    search_fields = (
        'materials__study__title',
    )
    ordering = ('materials__study', 'materials', 'number', 'condition')
    readonly_fields = (
        'slug',
        'materials',
    )
    inlines = (
        ItemQuestionInlineAdmin,
        ItemFeedbackInlineAdmin,
    )

    def item(self, obj):
        return str(obj)

    def study(self, obj):
        return obj.materials.study
    study.admin_order_field = 'materials__study'


@admin.register(models.TextItem)
class TextItemAdmin(ItemAdminMixin, admin.ModelAdmin):
    list_display = (
        'item',
        'study',
        'materials',
        'text',
    )


@admin.register(models.MarkdownItem)
class MarkdownItemAdmin(ItemAdminMixin, admin.ModelAdmin):
    list_display = (
        'item',
        'study',
        'materials',
        'text',
    )
    formfield_overrides = {
        TextField: {'widget': MarkdownxAdminWidget},
    }


@admin.register(models.AudioLinkItem)
class AudioLinkItemAdmin(ItemAdminMixin, admin.ModelAdmin):
    list_display = (
        'item',
        'study',
        'materials',
        'urls',
    )


@admin.register(models.ItemList)
class ItemListAdmin(admin.ModelAdmin):
    date_hierarchy = 'materials__study__created_date'
    list_display = (
        'number',
        'study',
        'materials',
    )
    list_per_page = 32
    search_fields = (
        'materials__study__title',
    )
    ordering = ('materials__study', 'materials', 'number')
    readonly_fields = (
        'materials',
    )

    def study(self, obj):
        return obj.materials.study
    study.admin_order_field = 'materials__study'

    def get_form(self, request, obj=None, change=False, **kwargs):
        self.obj = obj
        return super().get_form(request, obj, change, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'items':
            kwargs['queryset'] = models.Item.objects.filter(materials=self.obj.materials)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
