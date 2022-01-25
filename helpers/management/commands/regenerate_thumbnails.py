import logging
import time

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
                    ok = False

                    for attempt in range(5):
                        logging.info(
                            'Generating thumbnail for %s (%s/%s)', obj, attempt + 1, 5)

                        try:
                            obj.generate_pdf_thumbnail()
                            ok = True
                            break

                        except Exception as ex:
                            logging.warn(
                                'Thumbnail generation attempty failed. Reason: %s', ex)
                            # time.sleep(5)

                    if not ok:
                        logging.error(
                            'Thumbnail generation failed for %s', obj)
