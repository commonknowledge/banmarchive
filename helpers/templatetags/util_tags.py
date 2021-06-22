from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from webpack_loader.templatetags import webpack_loader
register = template.Library()


@register.inclusion_tag('helpers/bs_link.html', takes_context=True)
def bs_link(context, **kwargs):
    kwargs['request'] = context.get('request')
    return kwargs
