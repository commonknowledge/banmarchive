import re
from sys import intern

import dateparser
from bs4 import BeautifulSoup
from django.conf import settings

from helpers import parsing as ps


def crawl_7days():
    html = parse_html(get_root('7days'))

    root = html.find('table').find_all('td')[1]
    stream = extract_stream(root)

    return {
        'title': '7 Days',
        'type': 'multi',
        'issues': ps.parse(ps.multiple(parse_issue), stream)
    }


def crawl_blackdwarf():
    html = parse_html(get_root('blackdwarf'))
    root = html.find('table').find_all('td')[1].find_all('p')[1]
    stream = extract_stream(root)

    return {
        'title': 'Black Dwarf',
        'type': 'simple',
        'issues': ps.parse(ps.multiple(parse_simple_issue), stream)
    }


def crawl_newreasoner():
    html = parse_html(get_root('nr'))
    root = html.find('table').find_all('td')[1]
    for el in root.select('i br') + root.select('em br'):
        el.decompose()

    stream = extract_stream(root)

    return {
        'title': 'New Reasoner',
        'type': 'multi',
        'issues': ps.parse(ps.multiple(parse_issue_nr), stream)
    }


def get_root(slug):
    root = settings.BASE_DIR + '/website'
    publication_path = root + '/collections/' + slug
    return publication_path + '/index.htm'


def parse_html(path):
    with open(path, 'r') as file:
        return BeautifulSoup(file.read(), 'html.parser')


def extract_stream(root):
    internal_links = root.find_all(
        lambda node: node.name == 'a' and not node.attrs.get('href', '').endswith('.pdf'))
    whitespace = root.find_all(lambda node: node.get_text().strip() == '')

    for node in internal_links + whitespace:
        node.decompose()

    def should_strip(d):
        if getattr(d, 'name') == 'br':
            return False

        text = ps.trimmed(d)
        return text in ('', ';')

    stream = list(x for x in root.descendants if not should_strip(x))
    stripped = list(x for x in root.descendants if should_strip(x))

    for d in stripped:
        if hasattr(d, 'decompose') and not d.decomposed:
            d.decompose()
        else:
            if hasattr(d, 'parent'):
                d.extract()

    return stream


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

parse_article_nr_a = ps.mapped(
    ps.sequence(
        ps.parse_pdf_link,
        ps.optional(ps.as_text(ps.element(('i', 'em')))),
    ),
    lambda link, string: {
        'title': link['content'],
        'pdf': link['href'],
        'author': string
    }
)

parse_article_nr_b = ps.mapped(
    ps.sequence(
        ps.filtered(
            ps.parse_text,
            lambda x: x.endswith(':')
        ),
        ps.parse_pdf_link,
    ),
    lambda author, link: {
        'title': link['content'],
        'pdf': link['href'],
        'author': author.replace(':', '').strip()
    }
)

parse_article_nr = ps.any_of(
    parse_article_nr_a,
    parse_article_nr_b
)

parse_issue_nr = ps.mapped(
    ps.sequence(
        ps.element(lambda x: ps.has_class(x, 'headerlarge')),
        ps.delimited(parse_article_nr, ps.multiple(
            ps.element('br', deep=False)))
    ),
    lambda title, articles: {
        'title': title,
        'date': ps.seasonal_date(title),
        'articles': articles
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

parse_issue_v2 = ps.mapped(
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
        'date': ps.after_markers(link['content'], VOL_NO_BDWARF, dateparser.parse),
        'pdf': link['href'],
    }
)
