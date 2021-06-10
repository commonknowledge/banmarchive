import re
import io
from typing import Any

from pgmagick import Blob, Image, Geometry
from PyPDF3 import PdfFileReader, PdfFileWriter
from django.core.files.base import ContentFile
from wagtail.images.models import Image as WagtailImage

PdfThumbnailMixinSubclasses = []


class PdfThumbnailMixin:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        PdfThumbnailMixinSubclasses.append(cls)

    thumbnail_attribute = 'thumbnail'

    def get_thumbnail_document(self) -> Any:
        pass

    def generate_pdf_thumbnail(self, save=True):
        document = self.get_thumbnail_document()
        if document is None or document.file is None:
            return

        with document.file.storage.open(document.file.name, 'rb') as fd:
            imagename = get_basename(document.file.name) + '_preview.jpeg'
            image_file = generate_pdf_thumbnail(
                fd, filename=imagename, height=1440)

        image_model = getattr(self, self.thumbnail_attribute)
        if image_model is None:
            image_model = WagtailImage()
            setattr(self, self.thumbnail_attribute, image_model)

        image_model.file = image_file
        image_model.save()

        if save:
            self.save(generate_thumbnail=False)

    def has_pdf_thumbnail(self):
        image = getattr(self, self.thumbnail_attribute, None)
        return image is not None and image.file is not None

    def save(self, *args, generate_thumbnail=True, **kwargs):
        if generate_thumbnail and not self.has_pdf_thumbnail():
            self.generate_pdf_thumbnail(save=False)

        return super().save(*args, **kwargs)


def generate_pdf_thumbnail(data, filename, page_number=0, height=800):
    # First, extract from the pdf doc the page we want a preview from
    pdf_source = PdfFileReader(data)
    pdf_temp = PdfFileWriter()
    page_buf = io.BytesIO()

    page = pdf_source.getPage(page_number)
    pdf_temp.addPage(page)

    # Next, write the page into a temporary buffer, then render a thumbnail
    pdf_temp.write(page_buf)
    page_buf.seek(0)

    in_blob = Blob(page_buf.read())
    image = Image(in_blob)
    geom = image.size()
    width = geom.width() / geom.height() * height
    image.zoom(Geometry(int(width), int(height)))

    out_blob = Blob()
    image.magick('JPEG')
    image.write(out_blob)

    return ContentFile(out_blob.data, filename)


def get_basename(url):
    components = url.split('/')
    last = components[len(components) - 1]
    return re.sub(r'\.\w+$', '', last)
