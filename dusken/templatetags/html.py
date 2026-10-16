import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def sanitize_html(value):
    return mark_safe(nh3.clean(value))  # noqa: S308 - nh3 strips unsafe tags and attributes
