from datetime import date
from helpers.content import get_page, safe_to_int
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
    mode = request.GET.get('mode', 'simple')

    if mode == 'advanced':
        return advanced_search(request)

    search_query = request.GET.get('query')
    scope_id = safe_to_int(request.GET.get('scope'))
    scope = Page.objects.filter(
        pk=scope_id
    ).first() if scope_id is not None else None

    page = get_page(request)

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
        qs = models.Article.objects.live()

        if scope is not None:
            qs = qs.descendant_of(scope)

        search_results = qs.search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 25)

    search_results = tuple(
        {'page': page, 'search_highlight': get_search_highlight(
            page.specific, highlighter)}
        for page in paginator.page(page)
    )

    return TemplateResponse(request, 'search/search.html', {
        'scope': scope,
        'publications': models.Publication.objects.order_by('title'),
        'search_query': search_query,
        'search_results': search_results,
        'total_count': paginator.count,
        'paginator': paginator,
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
            request.GET.getlist('bools'),
            request.GET.getlist('ops'),
            request.GET.getlist('values')
        )
    )

    base_response = {
        'decades': get_decades,
        'publications': get_publications
    }

    if len(search_terms) > 0:
        publication = request.GET.get('publication')
        decade = request.GET.get('decade')
        author = request.GET.get('author')
        page = get_page(request)

        filter = and_all(
            get_advanced_search_base_filter(
                publication, decade, author),
            get_advanced_search_boolean_filter(search_terms)
        )

        if filter is not None:
            objects = models.AdvancedSearchIndex.objects.filter(filter)
        else:
            objects = models.AdvancedSearchIndex.objects.all()

        paginator = Paginator(objects, per_page=25)
        search_results = (
            page.page_id
            for page in paginator.page(page).object_list
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
                         ['publication', safe_to_int(publication)]])

    if decade:
        q = add_to_query(q, keywords__contains=[
                         ['decade', safe_to_int(decade)]])

    if author:
        q = add_to_query(q, keywords__contains=[['author', author.lower()]])

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
                **get_advanced_search_term(op, value),
                negate=(bool_op == 'NOT'))

    or_q = None
    for term in ors:
        bool_op = term['bool']
        value = term['value']
        op = term['op']

        if value:
            or_q = add_to_query(
                or_q,
                **get_advanced_search_term(op, value),
                op='or')

    return and_all(and_q, or_q, op='or')


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
        return {'keywords__regex': value.lower()}
    else:
        return {'keywords__contains': value.lower()}


def add_decade(prevdate):
    return date(prevdate.year + 10, prevdate.month, prevdate.day)
