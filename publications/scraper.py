from collections import defaultdict
import os
import re
from urllib.parse import unquote, urlencode
from os import path
import datetime

import dateparser
import requests
from bs4 import BeautifulSoup, Comment
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

        exists = requests.get(
            endpoint + f'/api/documents/query/?{urlencode({"title": title})}', auth=auth)
        if exists.ok:
            return exists.json()['id']

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

                if cover_id is None:
                    cover_article = issue_data['articles'][0]

                    cover_id = upload_document(
                        pub_data,
                        cover_article['pdf'],
                        cover_name + ': ' + cover_article['title']
                    )

                issue_resource = post_to('issues/multi', json={
                    'slug': slugify(issue_data['title']),
                    'title': issue_data['title'],
                    'publication_date': issue_data.get('date'),
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

    # upload_publication(crawl_7days())
    # upload_publication(crawl_blackdwarf())
    upload_publication(crawl_newuniversity())
    upload_publication(crawl_redrag())
    upload_publication(crawl_authors_and_titles('nr_meta', 'New Reasoner'))
    upload_publication(crawl_authors_and_titles(
        'mt', 'Marxism Today', get_mt_covers()))
    upload_publication(crawl_authors_and_titles(
        'soundings', 'Soundings', get_issue_cover('soundings')))
    upload_publication(crawl_authors_and_titles(
        'ulr_meta', 'Universities & Left Review', get_issue_cover('ulr')))


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


def crawl_newuniversity():
    html = parse_html(get_root('newuniversity'))

    root = html.find('table').find_all('td')[1]
    stream = extract_stream(root)

    return {
        'title': 'New University',
        'path': get_root('newuniversity'),
        'type': 'multi',
        'issues': ps.parse(ps.multiple(parse_issue_newuniversity), stream)
    }


def crawl_authors_and_titles(root, pub_title, get_cover=lambda *args, **kwargs: None):
    indexdir = get_root(f'authorsandtitles/{root}', '')
    issues = defaultdict(lambda: [])

    for filename in os.listdir(indexdir):
        if not filename.endswith('.htm'):
            continue

        html = parse_html(get_root('authorsandtitles/' + root, '/' + filename))
        table = html.find('table')
        if table is None:
            continue

        text = ps.trimmed(table)

        def keyword(kw):
            return extract_group(f'{kw} ?(.*?) ?(author:|source:|title:|$)', text)

        author = keyword('author:')
        source = keyword('source:')
        title = keyword('title:')
        pdf = table.find('embed')['src']
        assert source and (title or author) and pdf
        assert path.exists(indexdir + '/' + pdf)

        issues[source].append({
            'author': author,
            'title': title,
            'pdf': pdf
        })

    def to_issue(source, articles):
        assert extract_date(source)
        issue = extract_group(r'issue (\d+)', source, int)

        return {
            'title': source.replace(pub_title, '').strip(),
            'date': extract_date(source),
            'issue': issue,
            'articles': articles,
            'pdf': get_cover(date=extract_date(source), issue=issue)
        }

    return {
        'title': pub_title,
        'path': indexdir + '/index.htm',
        'type': 'multi',
        'issues': tuple(
            to_issue(source, articles) for source, articles in issues.items()
        )
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


def crawl_redrag():
    html = parse_html(get_root('redrag'))

    root = html.find('table').find_all('td')[1]
    stream = extract_stream(root)

    return {
        'title': 'Red Rag',
        'path': get_root('redrag'),
        'type': 'multi',
        'issues': ps.parse(ps.multiple(parse_issue_redrag), stream)
    }


def get_mt_covers():
    base = 'http://banmarchive.org.uk/collections/mt/nosearchable/'
    res = requests.get(base)
    html = res.text
    table = BeautifulSoup(html, 'html.parser').find('ul')

    def is_cover_for_date(date: datetime.date, text: str):
        month = f'0{date.month}' if date.month < 10 else str(date.month)
        year = str(date.year % 100)

        return 'cov' in text.lower() and month in text and year in text

    def download(url: str):
        tmpfile = get_tmp(url.replace('/', '__'))

        if not os.path.exists(tmpfile):
            res = requests.get(base + url)

            with open(tmpfile, 'wb') as f:
                for chunk in res.iter_content(chunk_size=512 * 1024):
                    if chunk:
                        f.write(chunk)

        return '../../../../' + tmpfile

    def get_mt_cover(date: datetime.date, **kwargs):
        return next(download(a['href']) for a in table.find_all('a') if is_cover_for_date(date, ps.trimmed(a)))

    return get_mt_cover


def get_issue_cover(slug):
    base = f'website/collections/{slug}/'
    covers = os.listdir(base)

    def is_cover_for_issue(issue: int, text: str):
        opts = (f'{issue}_', f'0{issue}_', f'00{issue}_')
        if not 'cov' in text.lower():
            return False

        return bool(
            next(
                (o for o in opts if o in text),
                None
            )
        )

    def get_cover(issue: int = None, **kwargs):
        return next(
            (f'../../{slug}/' +
             file for file in covers if is_cover_for_issue(issue, file)),
            None
        )

    return get_cover


def get_tmp(slug):
    try:
        os.mkdir('.tmp')
    except:
        pass

    return f'.tmp/{slug}'


def get_root(slug, file='/index.htm'):
    root = settings.BASE_DIR + '/website'
    publication_path = root + '/collections/' + slug
    return publication_path + file


def parse_html(path):
    with open(path, 'r') as file:
        return BeautifulSoup(file.read(), 'html.parser')


def extract_stream(root):
    def matches(d, sel):
        return d.name == sel or d.find(sel)

    def should_strip(d):
        if isinstance(d, Comment):
            return True

        if getattr(d, 'name') == 'br':
            return False

        if matches(d, 'embed'):
            return False

        text = ps.trimmed(d)
        return text in ('', ';')

    internal_links = root.find_all(
        lambda node: node.name == 'a' and not node.attrs.get('href', '').endswith('.pdf'))

    whitespace = root.find_all(
        lambda node: node.name != 'embed' and node.get_text().strip() == '')

    for node in internal_links + whitespace:
        if matches(node, 'embed'):
            continue

        node.decompose()

    stream = list(x for x in root.descendants if not should_strip(x))
    stripped = list(x for x in root.descendants if should_strip(x))

    for d in stripped:
        if hasattr(d, 'decompose') and not d.decomposed:
            d.decompose()
        else:
            if hasattr(d, 'parent'):
                d.extract()

    return list(x for x in stream if not isinstance(x, str) or x.strip() != '')


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

parse_article_newuniversity = ps.mapped(
    ps.sequence(
        ps.parse_pdf_link,
        ps.optional(ps.parse_text)
    ),
    lambda link, author: {
        'title': link['content'],
        'pdf': link['href'],
        'author': author
    }
)

parse_article_redrag = ps.any_of(
    ps.mapped(
        ps.sequence(ps.parse_pdf_link),
        lambda link: {
            'title': link['content'],
            'pdf': link['href'],
        }
    ),
    ps.mapped(
        ps.sequence(
            ps.element('em'),
            ps.parse_pdf_link,
        ),
        lambda author, link: {
            'title': link['content'],
            'pdf': link['href'],
            'author': author
        }
    ),
)

ISSUE_NU = re.compile(r'issue\s+(\d+)', re.IGNORECASE)
DATE_NU = re.compile(r'\w+ +19\d\d', re.IGNORECASE)
parse_issue_newuniversity = ps.mapped(
    ps.header_body(
        ps.element(lambda e: ISSUE_NU.search(ps.trimmed(e))),
        parse_article_newuniversity,
    ),
    lambda title, articles: {
        'title': title,
        'date': extract_date(title),
        'pdf': articles[0]['pdf'],
        'issue': extract_group(ISSUE_NU, title, int),
        'articles': articles[1:]
    }
)

ISSUE_RR = re.compile(r'volume\s+(\d+)', re.IGNORECASE)
parse_issue_redrag = ps.mapped(
    ps.header_body(
        ps.element(lambda e: ISSUE_RR.search(ps.trimmed(e))),
        parse_article_redrag,
    ),
    lambda title, articles: {
        'title': title,
        'pdf': articles[0]['pdf'],
        'issue': extract_group(ISSUE_RR, title, int),
        'volume': extract_group(ISSUE_RR, title, int),
        'articles': articles[1:]
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
            date = parse_date(c)
            if date is not None:
                return date

    date = r"(january|february|march|april|may|june|july|august|september|october|november|december) +\d+"
    hits = re.search(date, datestr, re.IGNORECASE)
    if hits is not None and hits.group(0):
        return parse_date('1 ' + hits.group(0))

    return ps.seasonal_date(datestr)


def parse_date(str):
    dt = dateparser.parse(str.strip())

    if dt is not None and dt.year != datetime.date.today().year:
        return dt.date()


def remove(patterns, string):
    for p in patterns:
        string = re.sub(p, '', string, flags=re.IGNORECASE)

    return string


def extract_group(patterns, string, fn=None, i=1):
    if isinstance(patterns, str) or isinstance(patterns, re.Pattern):
        patterns = (patterns,)

    for pattern in patterns:
        if isinstance(pattern, re.Pattern):
            match = pattern.search(string)
        else:
            match = re.search(pattern, string, re.IGNORECASE)
        if match is not None:
            g = match.group(i)
            return g if fn is None else fn(g)
