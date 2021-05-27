import re

import dateparser
from bs4 import BeautifulSoup
from django.conf import settings

from helpers import parsing as ps


def crawl_7days():
    html = parse_html(get_root('7days'))

    table = html.find('table').find_all('td')
    table.pop(0)

    stream = list(table.pop(0).descendants)
    stream = ps.filter_stream(ignored, stream)
    return {
        'title': '7 Days',
        'type': 'multi',
        'issues': ps.parse(ps.multiple(parse_issue), stream)
    }


def crawl_blackdwarf():
    html = parse_html(get_root('blackdwarf'))

    table = html.find('table').find_all('td')
    table.pop(0)

    stream = list(table.pop(0).descendants)
    stream = ps.filter_stream(ignored, stream)
    return {
        'title': 'Black Dwarf',
        'type': 'simple',
        'issues': ps.parse(ps.multiple(parse_simple_issue), stream)
    }


def get_root(slug):
    root = settings.BASE_DIR + '/website'
    publication_path = root + '/collections/' + slug
    return publication_path + '/index.htm'


def parse_html(path):
    with open(path, 'r') as file:
        return BeautifulSoup(file.read(), 'html.parser')


ignored = ps.any_of(
    ps.parse_whitespace,
    ps.parse_internal_link
)

parse_article = ps.mapped(
    ps.sequence(
        ps.parse_pdf_link,
        ps.optional(ps.parse_text)
    ),
    lambda link, text: {
        'title': link['content'],
        'pdf': link['href'],
        'intro': text
    }
)

VOL_NO_7DAYS = re.compile('(vol\\.? \\d+)? no.? \\d+', re.IGNORECASE)
def VOL_NO_BDWARF(str): return str.rfind(' - ')


parse_issue = ps.mapped(
    ps.sequence(
        ps.element(lambda e: VOL_NO_7DAYS.search(ps.trimmed(e))),
        ps.parse_pdf_link,
        ps.optional(ps.parse_text),
        ps.multiple(parse_article)
    ),
    lambda title, cover, cover_credit, articles: {
        'title': ps.trimmed(title),
        'date': ps.upto_markers(title, VOL_NO_7DAYS, dateparser.parse),
        'pdf': cover['href'],
        'articles': articles
    }
)

parse_simple_issue = ps.mapped(
    ps.sequence(
        ps.parse_pdf_link
    ),
    lambda link: {
        'title': ps.trimmed(link['content']),
        'date': ps.after_markers(ps.trimmed(link), VOL_NO_BDWARF, dateparser.parse),
        'pdf': link['href'],
    }
)
