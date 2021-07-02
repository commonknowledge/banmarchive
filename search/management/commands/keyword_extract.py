from django.db import transaction
from publications.models import Article

from django.core.management.base import BaseCommand

from search.models import KeywordExtractor


class Command(BaseCommand):
    help = 'Regenerate article keywords'

    def add_arguments(self, parser):
        parser.add_argument(
            '--training_limit',
        )
        parser.add_argument(
            '--all',
            action='store_const',
            const=True
        )
        parser.add_argument(
            '--train',
            action='store_const',
            const=True
        )

    def handle(self, all=False, train=False, training_limit=None, *args, **kwargs):
        extractor = KeywordExtractor.article_extractor()

        if train or not extractor.is_trained:
            articles = Article.objects.filter()
            if training_limit is not None:
                articles = articles[:-int(training_limit)]

            print(f'training model on {articles.count()} articles...')
            extractor.train_model(articles)

        if all:
            articles = Article.objects.filter()
        else:
            articles = Article.objects.filter(tagged_items=None)

        print(f'fitting {articles.count()} articles...')

        extractor.fit_keywords(articles)
