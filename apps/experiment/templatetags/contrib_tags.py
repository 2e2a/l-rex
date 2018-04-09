from django import template

register = template.Library()


@register.filter
def bootstrap_alert_class(message_level):
    if message_level == 'debug':
        return 'alert-dark'
    if message_level == 'info':
        return 'alert-primary'
    if message_level == 'success':
        return 'alert-success'
    if message_level == 'warning':
        return 'alert-warning'
    if message_level == 'error':
        return 'alert-danger'