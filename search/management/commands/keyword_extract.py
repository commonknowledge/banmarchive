from django.db import transaction
from publications.models import Article, SimpleIssue

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
        parser.add_argument(
            '--no_keyword_extract',
            action='store_const',
            const=True
        )

    def handle(self, all=False, no_keyword_extract=False, *args, **kwargs):
        for model in [Article, SimpleIssue]:
            if all:
                articles = model.objects.filter()
            else:
                articles = model.objects.filter(tagged_items=None)

            print(f'fitting {articles.count()} {model.__name__}...')

            iterator = articles.specific().iterator()

            if no_keyword_extract:
                for article in iterator:
                    article.save(generate_keywords=False)
            else:
                extract_keywords(iterator)
