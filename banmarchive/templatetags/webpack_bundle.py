from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from webpack_loader.templatetags import webpack_loader
register = template.Library()


@register.simple_tag
def webpack_bundle(name, type='js'):
    if settings.DEBUG:
        if type == 'js':
            return mark_safe(f'<script src="http://localhost:8080/{name}.js"></script>')
        else:
            return mark_safe('')

    else:
        return webpack_loader.render_bundle(name, type)
