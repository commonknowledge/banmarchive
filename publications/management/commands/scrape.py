
import requests
from django.template.defaultfilters import last, slugify
from django.core.management.base import BaseCommand

from publications import models, serializers, scraper


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
