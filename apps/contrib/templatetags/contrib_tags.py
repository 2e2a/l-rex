from markdownx.utils import markdownify as markdownx_markdownify

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def bootstrap_alert_class(message_level):
    if message_level == 'debug':
        return 'alert-dark'
    if message_level == 'info':
        return 'alert-light'
    if message_level == 'success':
        return 'alert-dark'
    if message_level == 'warning':
        return 'alert-dark'
    if message_level == 'error':
        return 'alert-dark'


@register.filter
def markdownify(text):
    if text:
        return mark_safe(markdownx_markdownify(text))
