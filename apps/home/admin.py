from django.contrib import admin

from . import models


class NewsAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)


admin.site.register(models.News, NewsAdmin)
