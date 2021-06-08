from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
from django.contrib.postgres.search import SearchHeadline, SearchQuery
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join

from wagtail.core.models import Page
from wagtail.search.models import Query


def search(request):
    search_query = request.GET.get('query', None)
    page = request.GET.get('page', 1)

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
        search_results = Page.objects.live().search(search_query)

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
        'total_count': paginator.count
    })


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
