from django.contrib import admin

from . import models


@admin.register(models.TextItem)
class TextItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'materials__study__created_date'
    list_display = (
        'item',
        'study',
        'materials',
        'text',
    )
    list_per_page = 32
    search_fields = (
        'materials__study__title',
    )

    def item(self, obj):
        return str(obj)

    def study(self, obj):
        return obj.materials.study


@admin.register(models.AudioLinkItem)
class AudioLinkItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'materials__study__created_date'
    list_display = (
        'item',
        'study',
        'materials',
        'urls',
    )
    list_per_page = 32
    search_fields = (
        'materials__study__title',
    )

    def item(self, obj):
        return str(obj)

    def study(self, obj):
        return obj.materials.study


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

    def study(self, obj):
        return obj.materials.study


@admin.register(models.ItemQuestion)
class ItemQuestionAdmin(admin.ModelAdmin):
    date_hierarchy = 'item__materials__study__created_date'
    list_display = (
        'item_question',
        'study',
        'materials',
    )
    list_per_page = 32
    search_fields = (
        'item__materials__study__title',
    )

    def item_question(self, obj):
        return '{}-{}'.format(str(obj.item), obj.number)

    def materials(self, obj):
        return obj.item.materials

    def study(self, obj):
        return self.materials(obj).study
