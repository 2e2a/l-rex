from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from . import models


class ProfileInline(admin.StackedInline):
    model = models.UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class ProfileUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'date_joined', 'is_staff')
    ordering = ('date_joined',)


admin.site.unregister(User)
admin.site.register(User, ProfileUserAdmin)
