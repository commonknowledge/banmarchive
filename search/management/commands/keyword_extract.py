from django.db import transaction
from publications.models import Article

from django.core.management.base import BaseCommand

from search.models import extract_keywords


class Command(BaseCommand):
    help = 'Regenerate article keywords'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_const',
            const=True
        )

    def handle(self, all=False, train=False, training_limit=None, *args, **kwargs):
        if all:
            articles = Article.objects.filter()
        else:
            articles = Article.objects.filter(tagged_items=None)

        print(f'fitting {articles.count()} articles...')

        extract_keywords(articles)
