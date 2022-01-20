import logging

from django.db import transaction
from publications.models import Article

from django.core.management.base import BaseCommand

from search.models import AdvancedSearchIndex, IndexedPdfMixinSubclasses


class Command(BaseCommand):
    help = 'Reindex the text content of pdf files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_const',
            const=True
        )

    @transaction.atomic
    def handle(self, *args, all=False, **kwargs):
        for cls in IndexedPdfMixinSubclasses:
            logging.info('Found %s instances of %s to index',
                         cls.objects.all().count(), cls)

            for obj in cls.objects.all().iterator():
                if not obj.has_indexed_pdf_content() or all:
                    logging.info('Reindexing %s', obj)
                    obj.reindex_pdf_content()

                if not obj.has_summary() or all:
                    logging.info('Regenerating summary for %s', obj)
                    obj.regenerate_summary()
