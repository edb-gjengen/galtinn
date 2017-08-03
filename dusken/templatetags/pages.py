from django import template
from django.utils.translation import get_language

register = template.Library()


@register.simple_tag
def get_language_page_prefix():
    return '/{}/'.format(get_language())
