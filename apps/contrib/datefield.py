from django import forms
from django.db import models


class DateInput(forms.DateInput):
    def __init__(self, attrs={}, **kwargs):
        defaults = {
            'placeholder': 'yyyy-mm-dd',
            'type': 'date',
        }
        defaults.update(attrs)
        super().__init__(format='%Y-%m-%d', attrs=defaults, **kwargs)


class DateFormField(forms.DateField):
    widget = DateInput


class DateField(models.DateField):
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', DateFormField)
        return super().formfield(**kwargs)
