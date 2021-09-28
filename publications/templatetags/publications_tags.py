from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from webpack_loader.templatetags import webpack_loader
register = template.Library()


@register.inclusion_tag('publications/issue_card.html')
def issue_card(issue):
    return {
        'issue': issue
    }


@register.inclusion_tag('publications/publication_card.html')
def publication_card(issue):
    return {
        'issue': issue
    }
