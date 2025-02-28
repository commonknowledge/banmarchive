import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.documents.models import Document
from .migrate_awards import migrate_data
import logging


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def process_xml_on_upload(sender, instance, **kwargs):
    """Runs when a new document is uploaded or updated in Wagtail."""
    if os.path.basename(instance.file.name) == "awards.xml":
        logger.info(f"Processing XML file: {instance.file.path}")
        migrate_data(instance.file.path)
    else:
        logger.info(f"Skipping non-XML file: {instance.file.name}")
