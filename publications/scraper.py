import re
from urllib.parse import unquote
from os import path
import datetime

import dateparser
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.text import slugify

from helpers import parsing as ps


def scrape(endpoint, auth, root_id):
    def post_to(route, json=None, **kwargs):
        url = endpoint + '/api/' + route + '/'
        print('POST', url, json if json else kwargs.get('data'))

        res = requests.post(url, json=prep_json(json), auth=auth, **kwargs)
        if not res.ok:
            if res.status_code == 500:
                raise IOError('Application Error')

            raise IOError(res.text)

        return res.json()

    def upload_document(pub, doc, title):
        if doc is None:
            return None

        pathroot = path.dirname(pub['path'])
        docpath = unquote(pathroot + '/' + doc)

        with open(docpath, 'rb') as file:
            doc_resource = post_to('documents', data={
                'title': title,
            }, files={'file': file})

        return doc_resource['id']

    def upload_publication(pub_data):
        pub_resource = post_to('publications', json={
            'slug': slugify(pub_data['title']),
            'title': pub_data['title'],
            'parent': root_id,
            'tags': ()
        })

        if pub_data['type'] == 'multi':
            for issue_data in pub_data['issues']:
                cover_name = pub_data['title'] + ' ' + issue_data['title']

                cover_id = upload_document(
                    pub_data, issue_data['pdf'], cover_name)

                issue_resource = post_to('issues/multi', json={
                    'slug': slugify(issue_data['title']),
                    'title': issue_data['title'],
                    'publication_date': issue_data['date'],
                    'issue_cover': cover_id,
                    'parent': pub_resource['id'],
                    'issue': issue_data.get('issue'),
                    'volume': issue_data.get('volume'),
                    'number': issue_data.get('number'),
                    'tags': ()
                })

                for article_data in issue_data['articles']:
                    doc_name = cover_name + ': ' + article_data['title']

                    content_id = upload_document(
                        pub_data, article_data['pdf'], doc_name)

                    post_to('articles', json={
                        'slug': slugify(article_data['title']),
                        'title': article_data['title'],
                        'article_content': content_id,
                        'parent': issue_resource['id'],
                        'intro_text': article_data.get('intro'),
                        'author_name': article_data.get('author'),
                        'tags': ()
                    })
        else:
            for issue_data in pub_data['issues']:
                doc_name = pub_data['title'] + ' ' + issue_data['title']

                content_id = upload_document(
                    pub_data, issue_data['pdf'], doc_name)

                issue_resource = post_to('issues/simple', json={
                    'slug': slugify(issue_data['title']),
                    'title': issue_data['title'],
                    'issue_content': content_id,
                    'publication_date': issue_data['date'],
                    'parent': pub_resource['id'],
                    'issue': issue_data.get('issue'),
                    'volume': issue_data.get('volume'),
                    'number': issue_data.get('number'),
                    'tags': ()
                })

    upload_publication(crawl_7days())
    upload_publication(crawl_blackdwarf())
    upload_publication(crawl_newreasoner())


def prep_json(obj):
    def prep_val(val):
        if isinstance(val, datetime.datetime):
            return val.isoformat()
        if isinstance(val, datetime.date):
            return val.isoformat()

        return val

    if obj is None:
        return None

    return dict({
        key: prep_val(val)
        for key, val
        in obj.items()
    })


def crawl_7days():
    html = parse_html(get_root('7days'))

    root = html.find('table').find_all('td')[1]
    stream = extract_stream(root)

    return {
        'title': '7 Days',
        'path': get_root('7days'),
        'type': 'multi',
        'issues': ps.parse(ps.multiple(parse_issue_7days), stream)
    }


def crawl_blackdwarf():
    html = parse_html(get_root('blackdwarf'))
    root = html.find('table').find_all('td')[1].find_all('p')[1]
    stream = extract_stream(root)

    return {
        'title': 'Black Dwarf',
        'path': get_root('blackdwarf'),
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
        'path': get_root('nr'),
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
            ps.element('br', deep=False)), term=ps.element('strong'))
    ),
    lambda title, articles: {
        'title': title,
        'date': ps.seasonal_date(title),
        'issue': extract_group(r'issue (\d+)', title, int),
        'pdf': None,
        'articles': articles
    }
)

VOL_NO_7DAYS = re.compile('(vol\\.? \\d+)? no.? \\d+', re.IGNORECASE)
def VOL_NO_BDWARF(str): return str.rfind(' - ')


parse_article_7days = ps.mapped(
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

issue_start = ps.element(lambda e: VOL_NO_7DAYS.search(ps.trimmed(e)))
parse_issue_7days = ps.mapped(
    ps.sequence(
        issue_start,
        ps.parse_pdf_link,
        ps.optional(ps.parse_text),
        ps.multiple(parse_article_7days, term=issue_start)
    ),
    lambda title, cover, cover_credit, articles: {
        'title': remove(('7 days', 'cover'), title),
        'date': extract_date(title),
        'pdf': cover['href'],
        'volume': extract_group(r'vol.? (\d+)', title, int),
        'number': extract_group((r'no.? (\d+)', r'number (\d+)'), title, int),
        'issue': extract_group(r'issue (\d+)', title, int),
        'articles': articles
    }
)

parse_simple_issue = ps.mapped(
    ps.sequence(
        ps.parse_pdf_link
    ),
    lambda link: {
        'title': ps.trimmed(link['content']),
        'date': extract_date(link['content']),
        'volume': extract_group(r'volume (\d+)', link['content'], int),
        'issue': extract_group(r'issue (\d+)', link['content'], int),
        'number': extract_group(r'number (\d+)', link['content'], int),
        'pdf': link['href'],
    }
)


def extract_date(datestr: str):
    seps = ('-', 'no', 'number', 'issue', 'vol')

    for sep in seps:
        components = datestr.lower().split(sep)
        for c in components:
            dt = dateparser.parse(c.strip())

            if dt is not None and dt.year != datetime.date.today().year:
                return dt.date()


def remove(patterns, string):
    for p in patterns:
        string = re.sub(p, '', string, flags=re.IGNORECASE)

    return string


def extract_group(patterns, string, fn=None, i=1):
    if isinstance(patterns, str):
        patterns = (patterns,)

    for pattern in patterns:
        match = re.search(pattern, string, re.IGNORECASE)
        if match is not None:
            g = match.group(i)
            return g if fn is None else fn(g)
