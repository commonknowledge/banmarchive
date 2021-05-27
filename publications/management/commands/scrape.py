
import re
import requests
import dateparser
from django.template.defaultfilters import last, slugify
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup

from publications import models, serializers
from helpers import parsing as ps


class Command(BaseCommand):
    help = 'Scrape a local archive and upload to the remote'

    serializer_map = {
        'issues/multi': serializers.MultiArticleIssueSerializer,
        'issues/simple': serializers.SimpleIssueSerializer,
        'articles': serializers.ArticleSerializer,
        'publications': serializers.PublicationSerializer
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--local',
        )
        parser.add_argument(
            '--remote',
        )
        parser.add_argument(
            '--auth',
        )
        parser.add_argument(
            '--dryrun',
            action='store_const',
            const=True
        )

    def handle(self, *args, local=None, remote=None, auth=None, dryrun=False, **kwargs):
        self.auth = auth
        self.remote = remote
        self.root = local
        self.dryrun = dryrun

        self.crawl_publication('7days')

    def crawl_publication(self, slug):
        publication_path = self.root + '/collections/' + slug
        index_path = publication_path + '/index.htm'
        index = self.parse_html(index_path)

        table = index.find('table').find_all('td')
        title = ps.trimmed(table.pop(0)).title()

        # The html is so inconsistently structured (and malformed) that we basically need to treat it as a token stream and parse that by hand using recursive descent.
        stream = list(table.pop(0).descendants)
        stream = ps.filter_stream(ignored, stream)

        publication = self.create_or_update(
            'publications', title=title, slug=slug, tags=(), parent=None)

        articles = ps.parse(ps.multiple(parse_issue), stream)
        print(articles)

    def parse_html(self, path):
        with open(path, 'r') as file:
            return BeautifulSoup(file.read(), 'html.parser')

    def create_or_update(self, resource, **data):
        serializer_class = self.serializer_map[resource]
        serializer = serializer_class(instance=data)
        json = serializer.data

        if self.dryrun:
            parent = data['parent']
            slug = data['slug']

            if parent is None:
                id = '/' + slug
            else:
                id = parent + '/' + slug

            json.update({'id': id})
            print(f'create {resource}:', json)
            return json

        url = self.remote + '/api' + resource + '/'
        auth = self.auth.split(':') if self.auth is not None else None

        res = requests.post(url, auth=auth, json=json)
        if not res.ok:
            raise IOError(f'create {resource}: http {res.status_code}')

        serializer = serializer_class(data=res.json())
        if not serializer.is_valid():
            raise IOError(serializer.error_message)

        return serializer.validated_data


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

VOL_NO = re.compile('(vol\\.? \\d+)? no.? \\d+', re.IGNORECASE)

parse_issue = ps.mapped(
    ps.sequence(
        ps.element(lambda e: VOL_NO.search(ps.trimmed(e))),
        ps.parse_pdf_link,
        ps.optional(ps.parse_text),
        ps.multiple(parse_article)
    ),
    lambda title, cover, cover_credit, articles: {
        'title': ps.trimmed(title),
        'date': ps.upto_markers(title, VOL_NO, dateparser.parse),
        'pdf': cover['href'],
        'articles': articles
    }
)
