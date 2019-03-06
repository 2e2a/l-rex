from django.contrib import admin

from . import models


@admin.register(models.TextItem)
class TextItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'experiment__study__created_date'
    list_display = (
        'item',
        'study',
        'experiment',
        'text',
    )
    list_per_page = 32
    search_fields = (
        'experiment__study__title',
    )

    def item(self, obj):
        return str(obj)

    def study(self, obj):
        return obj.experiment.study


@admin.register(models.AudioLinkItem)
class AudioLinkItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'experiment__study__created_date'
    list_display = (
        'item',
        'study',
        'experiment',
        'url',
    )
    list_per_page = 32
    search_fields = (
        'experiment__study__title',
    )

    def item(self, obj):
        return str(obj)

    def study(self, obj):
        return obj.experiment.study


@admin.register(models.ItemList)
class ItemListAdmin(admin.ModelAdmin):
    date_hierarchy = 'experiment__study__created_date'
    list_display = (
        'number',
        'study',
        'experiment',
    )
    list_per_page = 32
    search_fields = (
        'experiment__study__title',
    )

    def study(self, obj):
        return obj.experiment.study


@admin.register(models.ItemQuestion)
class ItemQuestionAdmin(admin.ModelAdmin):
    date_hierarchy = 'item__experiment__study__created_date'
    list_display = (
        'item_question',
        'study',
        'experiment',
    )
    list_per_page = 32
    search_fields = (
        'item_experiment__study__title',
    )

    def item_question(self, obj):
        return '{}-{}'.format(str(obj.item), obj.number)

    def experiment(self, obj):
        return obj.item.experiment

    def study(self, obj):
        return self.experiment(obj).study
