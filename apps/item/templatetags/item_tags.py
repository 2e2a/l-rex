from markdownx.utils import markdownify

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def markdownify_item(markdown_item):
    return mark_safe(markdownify(markdown_item.text))
