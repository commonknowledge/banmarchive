import logging

from django.core.management.base import BaseCommand

from helpers.thumbnail_generator import PdfThumbnailMixinSubclasses


class Command(BaseCommand):
    help = 'Regenerate preview images for pdf documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_const',
            const=True
        )

    def handle(self, *args, all=False, **kwargs):
        for cls in PdfThumbnailMixinSubclasses:
            if cls._meta.abstract:
                continue

            logging.info('Found %s instances of %s to generate thumbnails for',
                         cls.objects.all().count(), cls)

            for obj in cls.objects.all().iterator():
                if not obj.has_pdf_thumbnail() or all:
                    logging.info('Generating thumbnail for %s', obj)
                    obj.generate_pdf_thumbnail()
