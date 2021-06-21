from django import template

register = template.Library()


@register.inclusion_tag('search/search_block.html')
def search_block():
    return {}
