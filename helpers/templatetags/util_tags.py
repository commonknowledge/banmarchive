from wagtail.core.models import Site
from home.models import HomePage
from urllib import parse

from django import template
from django.conf import settings
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.utils.html import conditional_escape, format_html, format_html_join
from django.utils.safestring import mark_safe

from webpack_loader.templatetags import webpack_loader
register = template.Library()


@register.inclusion_tag('helpers/bs_link.html', takes_context=True)
def bs_link(context, **kwargs):
    kwargs['request'] = context.get('request')
    return kwargs


@register.inclusion_tag('helpers/menubar.html', takes_context=True)
def menubar(context, **kwargs):
    site = Site.find_for_request(context.get('request'))
    if site is None:
        return

    root = site.root_page
    kwargs['pages'] = root.get_children().in_menu()
    kwargs['request'] = context.get('request')

    return kwargs


@register.simple_tag(takes_context=True)
def bs_pagination(context, paginator: Paginator, **kwargs):
    request: HttpRequest = context.get('request')

    current_page = int(request.GET.get('page', 1))
    range_start = max(current_page - 2, 1)
    range_end = min(max(current_page + 2, range_start + 4),
                    paginator.num_pages)

    def get_page_link(i: int):
        params = request.GET.dict()
        params['page'] = i
        return request.path + '?' + parse.urlencode(params)

    first = format_html(
        '<li class="page-item"><a class="page-link" href="{}">First</a></li>',
        get_page_link(1),
    )

    last = format_html(
        '<li class="page-item"><a class="page-link" href="{}">Last</a></li>',
        get_page_link(paginator.num_pages),
    )

    pages = (
        format_html(
            '<li class="page-item{}"><a class="page-link" href="{}"{}>{}</a></li>',
            ' active' if i == current_page else '',
            get_page_link(i),
            ' aria-current="page"' if i == current_page else '',
            i
        )
        for i in range(range_start, range_end + 1)
    )

    list_items = mark_safe(conditional_escape('').join((first, *pages, last)))
    return format_html('<ul class="pagination">{}</ul>', list_items)
