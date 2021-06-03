from django.core.management.base import BaseCommand
from requests.auth import HTTPBasicAuth

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
            '--remote',
        )
        parser.add_argument(
            '--auth',
        )
        parser.add_argument(
            '--root',
        )

    def handle(self, *args, root, remote=None, auth=None, **kwargs):
        scraper.scrape(remote, auth=HTTPBasicAuth(
            *auth.split(':')), root_id=int(root))
