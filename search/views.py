from datetime import date
from django.core import paginator

from django.db.models.query_utils import Q
from helpers.cache import django_cached
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
from django.contrib.postgres.search import SearchHeadline, SearchQuery
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join

from wagtail.core.models import Page
from wagtail.search.models import Query

from publications import models


def search(request):
    page = request.GET.get('page', 1)
    mode = request.GET.get('mode', 'simple')

    if mode == 'advanced':
        return advanced_search(request)

    search_query = get_single(request, 'query')

    # Search
    if search_query:
        highlighter = SearchHeadline(
            'text_content',
            query=SearchQuery(search_query),
            min_words=60,
            max_words=80,
            start_sel='<banm:hl>',
            stop_sel="</banm:hl>"
        )
        search_results = models.Article.objects.live().search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)
    try:
        search_results_page = paginator.page(page)
    except PageNotAnInteger:
        search_results_page = paginator.page(1)
    except EmptyPage:
        search_results_page = paginator.page(paginator.num_pages)

    search_results = tuple(
        {'page': page, 'search_highlight': get_search_highlight(
            page.specific, highlighter)}
        for page in search_results_page
    )

    return TemplateResponse(request, 'search/search.html', {
        'search_query': search_query,
        'search_results': search_results,
        'total_count': paginator.count,
        'decades': get_decades,
        'publications': get_publications
    })


def get_decades():
    return (1950, 1960, 1970, 1980, 1990, 2000)


@django_cached('search.views.get_publications')
def get_publications():
    return models.Publication.objects.order_by('title')


def get_search_highlight(page, highlighter):
    if hasattr(page, 'text_content'):
        highlights_raw = type(page).objects.annotate(
            search_highlight=highlighter).get(id=page.id).search_highlight

        highlight_groups = list(
            hl.split('</banm:hl>')
            for hl in highlights_raw.split('<banm:hl>')
        )
        start = highlight_groups.pop(0)[0]

        highlights = tuple(
            format_html(
                '<span class="search-highlight">{}</span>{}',
                mark_safe(highlight),
                next,
            )
            for highlight, next in highlight_groups
        )

        return concat_html(start, *highlights)


def concat_html(*items):
    return format_html_join('', '{}', ((x,) for x in items))


def advanced_search(request):
    search_terms = tuple(
        {'bool': bool, 'op': op, 'value': value}
        for bool, op, value in zip(
            get_arr(request, 'bools'),
            get_arr(request, 'ops'),
            get_arr(request, 'values')
        )
    )

    base_response = {
        'decades': get_decades,
        'publications': get_publications
    }

    if len(search_terms) > 0:
        publication = get_single(request, 'publication')
        decade = get_single(request, 'decade')
        author = get_single(request, 'author')

        filter = and_all(
            get_advanced_search_base_filter(
                publication, decade, author),
            get_advanced_search_boolean_filter(search_terms)
        )

        if filter is not None:
            objects = models.AdvancedSearchIndex.objects.filter(filter)
        else:
            objects = models.AdvancedSearchIndex.objects.all()

        paginator = Paginator(objects, per_page=10)
        search_results = (
            page.page_id
            for page in paginator.page(1).object_list
        )

        return TemplateResponse(request, 'search/advanced.html', {
            **base_response,
            'filter': {
                'publication': publication,
                'decade': str(decade),
                'author': author
            },
            'terms': search_terms,
            'search_results': search_results if paginator.count > 0 else None,
            'paginator': paginator,
        })

    else:
        return TemplateResponse(request, 'search/advanced.html', base_response)


def get_advanced_search_base_filter(publication, decade, author):
    q = None

    if publication:
        q = add_to_query(q, keywords__contains=[
                         ['publication', int(publication)]])

    if decade:
        q = add_to_query(q, keywords__contains=[['decade', int(decade)]])

    if author:
        q = add_to_query(q, keywords__contains=[['author', author]])

    return q


def get_advanced_search_boolean_filter(search_terms):
    ors = tuple(t for t in search_terms if t['bool'] == 'OR')
    ands = tuple(t for t in search_terms if t['bool'] != 'OR')

    and_q = None
    for term in ands:
        bool_op = term['bool']
        value = term['value']
        op = term['op']

        if value:
            and_q = add_to_query(
                and_q,
                keywords__contains=value,
                negate=(bool_op == 'NOT'))

    or_q = None
    for term in ors:
        bool_op = term['bool']
        value = term['value']
        op = term['op']

        if value:
            or_q = add_to_query(
                or_q,
                keywords__contains=value,
                op='or')

    return and_all(and_q, or_q)


def and_all(*args, op='and', negate=False):
    lhs = None

    for rhs in args:
        if rhs is None:
            continue

        if negate:
            rhs = ~rhs

        if lhs is None:
            lhs = rhs
        elif op == 'and':
            lhs = lhs & rhs
        else:
            lhs = lhs | rhs

    return lhs


def add_to_query(lhs, op='and', negate=False, **kwargs):
    rhs = Q(**kwargs)
    return and_all(lhs, rhs, negate=negate, op=op)


def get_advanced_search_term(match, value):
    if match == 'contains':
        return {'keywords__0': 'tags', 'keywords__1__iregex': value}
    else:
        return {'keywords__0': 'tags', 'keywords__1': value}


def get_arr(request, key):
    val = request.GET.get(key, ())
    if isinstance(val, str):
        return (val,)

    return val


def get_single(request, key):
    arr = get_arr(request, key)
    return arr[0] if len(arr) > 0 else None


def add_decade(prevdate):
    return date(prevdate.year + 10, prevdate.month, prevdate.day)
