from datetime import date
import re
from typing import Match
from nltk.stem import PorterStemmer

from wagtail.contrib.postgres_search.backend import PostgresSearchBackend, PostgresSearchQueryCompiler
from helpers.content import get_page, safe_to_int
from django.core import paginator

from django.db.models.query_utils import Q
from helpers.cache import django_cached
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchConfig
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join, strip_tags

from wagtail.search.utils import parse_query_string, Phrase
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
        highlighter = create_highlighter(search_query)
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
        {
            'page': page,
            'search_highlight': get_search_highlight(
                page.specific,
                # Highight the full query or partial matches
                (*search_query.split(' '), search_query),
                highlighter,
                remove_partial=False
            )
        }
        for page in paginator.page(page)
    )

    return TemplateResponse(request, 'search/search.html', {
        'scope': scope,
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


def create_highlighter(*terms):
    '''
    Get sigils rather than raw html back from postgres so that we can safely escape the text highlight before formatting
    it.

    Not that an issue of marxism today from the 70s is likely to have an xss exploit embedded in it, but still...
    '''
    return SearchHeadline(
        'text_content',
        query=make_searchquery(*terms),
        max_fragments=3,
        fragment_delimiter='!!fragment!!',
        start_sel='!!start!!',
        stop_sel="!!stop!!"
    )


def get_search_highlight(page, terms, highlighter, remove_partial=True):
    if hasattr(page, 'text_content'):
        '''
        Calculate from the search result what to highlight.
        '''

        highlights_raw = type(page).objects.annotate(
            search_highlight=highlighter).get(id=page.id).search_highlight

        fragments = map(trim_frag, strip_tags(
            highlights_raw).split('!!fragment!!'))

        formatted = '<span class="search-frag-sep">…</span>'.join(fragments)
        formatted = ' '.join(re.split(r'[\n ]+', formatted))

        formatted = highight_phrases(
            formatted, terms, remove_partial=remove_partial)
        formatted = formatted.replace(
            '!!start!!', '<span class="search-highlight">')
        formatted = formatted.replace('!!stop!!', '</span>')

        return mark_safe(formatted)


def trim_frag(frag):
    '''
    Discard any parts of fragments that potentially span 'big' line breaks as these are
    likely to be across text blocks and hence look weird
    '''
    frag = next((x for x in re.split(r"\n\n+\n?", frag)
                 if '!!start!!' in x and '!!stop!!' in x), '')

    return frag.strip().strip('.')


def highight_phrases(headline, terms, remove_partial=True):
    '''
    For some reason, can't get postgres to only highlight full phrases rather than individual matched terms.
    Even when the query we're passing to the highlighter is clearly one that only returns full-phrase matches.

    Replace adjacent indivudual highights with the full highlight then remove any partial highlights.
    '''

    stemmer = PorterStemmer()
    terms = [t.lower() for t in terms]

    def replace_highighted(match: Match):
        words = ' '.join(match.groups())
        return f'!!start!!{words}!!stop!!'

    def replace_unhighligted(match: Match):
        words = ' '.join(match.groups())
        return words

    # Replace consecutive matches of all of a term's words with a match of the full term
    for term in terms:
        words = term.split(' ')
        if len(words) == 1:
            continue

        pattern = ' +'.join(
            f'!!start!! *({word}|{stemmer.stem(word)}\\w*) *!!stop!!'
            for word in words
        )

        headline, _ = re.subn(pattern, replace_highighted,
                              headline, flags=re.I)

    if remove_partial:
        # Remove any matches that are a subset of the full term
        for term in terms:
            words = term.split(' ')

            for word in words:
                if word in terms:
                    continue

                pattern = f'!!start!! *({word}|{stemmer.stem(word)}\\w*) *!!stop!!'
                headline, _ = re.subn(
                    pattern, replace_unhighligted, headline, flags=re.I)

    return headline


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
        'decades': lambda: [str(d) for d in get_decades()],
        'publications': get_publications
    }

    if len(search_terms) > 0:
        publication = request.GET.get('publication')
        decade = request.GET.get('decade')
        author = request.GET.get('author')
        page = get_page(request)

        filter = bool_op(
            get_advanced_search_base_filter(
                publication, decade, author),
            get_advanced_search_boolean_filter(search_terms, publication)
        )

        if filter is not None:
            objects = models.AdvancedSearchIndex.objects.filter(filter)
        else:
            objects = models.AdvancedSearchIndex.objects.all()

        paginator = Paginator(objects, per_page=25)

        fulltext_terms = [
            term['value']
            for term in search_terms
            if term['value']
            and not term['bool'] == 'NOT'
        ]
        highlighter = create_highlighter(*fulltext_terms)
        search_results = (
            {
                'highlight': get_search_highlight(page.page_id.specific, fulltext_terms, highlighter),
                'page': page.page_id.specific
            }
            for page in paginator.page(page).object_list
        )

        return TemplateResponse(request, 'search/advanced.html', {
            **base_response,
            'filter': {
                'publication': int(publication) if publication else '',
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


def get_advanced_search_boolean_filter(search_terms, publication):
    filter = None
    for term in search_terms:
        bool_op_type = term['bool']
        value = term['value']
        op = term['op']

        if not value:
            continue

        filter = bool_op(
            filter,
            get_advanced_search_term(op, value, publication),
            op=bool_op_type
        )

    return filter


def bool_op(*args, op='and', negate=False):
    op = op.lower()
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
        elif op == 'not':
            lhs = lhs & ~rhs
        else:
            lhs = lhs | rhs

    return lhs


def add_to_query(lhs, op='and', negate=False, **kwargs):
    rhs = Q(**kwargs)
    return bool_op(lhs, rhs, negate=negate, op=op)


def get_advanced_search_term(match, value, publication):
    if match == 'keyword':
        return Q(keywords__contains=value.lower())

    else:
        # Do a full-text search on each model type that supports it and 'join' on the advanced index using an IN
        # operator.
        #
        # This is far from an ideal way of doing it, and could perhaps be rewritten in a more efficient way,
        # but we're really up against the limits of what postgres can reasonably be expected to do with a search engine
        # right now.
        scope = Page.objects.filter(
            pk=int(publication)
        ).first() if publication else None

        pageids = set()

        # Make sure we don't DOS ourselves by sending too ridiculous a query to the database.
        # For reference this is about 3x the number of hits for the phrase 'women' at launch.
        MAX_FULLTEXT_HITS = 3000

        backend = PatchedPostgresSearchBackend()

        for type in (models.Article, models.SimpleIssue):
            qs = type.objects.live()
            if scope is not None:
                qs = qs.descendant_of(scope)

            res = backend.search(Phrase(value), qs, partial_match=False)
            if len(pageids) + len(res) < MAX_FULLTEXT_HITS:
                pageids.update(x.id for x in res)

        return Q(page_id__in=pageids)


def add_decade(prevdate):
    return date(prevdate.year + 10, prevdate.month, prevdate.day)


class PatchedPostgresSearchBackend(PostgresSearchBackend):
    def __init__(self):
        super().__init__({'SEARCH_CONFIG': 'english'})

    class PatchedPostgresSearchQueryCompiler(PostgresSearchQueryCompiler):
        '''
        Exact phrase matching is broken by the language configuration substituting stopwords, which although useful in
        the general case, is not wanted for exact phrase matching.

        Override the generation of postgres queries to not do stopword/synonym/etc substitution.
        '''
        query_compiler_class = PostgresSearchQueryCompiler

        def build_tsquery_content(self, query, config=None, invert=False):
            if isinstance(query, Phrase):
                return make_searchquery(query.query_string)

            return super().build_tsquery_content(query, config=config, invert=invert)

    query_compiler_class = PatchedPostgresSearchQueryCompiler


def make_searchquery(*terms):
    '''
    Where 'terms' is a list of phrases, match any of the full phrases identified by 'terms'
    '''

    q = None

    for t in terms:
        inner = '(' + ' <-> '.join(t.split(' ')) + ')'
        q = inner if q is None else q + ' || ' + q

    return SearchQuery(q, search_type='raw')
