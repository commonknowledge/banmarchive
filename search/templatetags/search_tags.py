from helpers.content import safe_to_int
from publications.models import Publication
from django import template

register = template.Library()


@register.inclusion_tag('search/search_block.html', takes_context=True)
def search_block(context, defined_scope=None, **kwargs):

    if defined_scope is None:
        scope = safe_to_int(context.get('request').GET.get('scope'))

    else:
        scope = defined_scope.id

    request = context.get('request')
    kwargs['search_query'] = request.GET.get('query')
    kwargs['defined_scope'] = defined_scope
    kwargs['scope'] = scope

    if scope is not None:
        kwargs['scope_param'] = '&' + str(scope)

    if not defined_scope:
        kwargs['publications'] = Publication.objects.all().order_by('title')

    return kwargs
