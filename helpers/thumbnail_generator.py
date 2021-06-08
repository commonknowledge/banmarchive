from pgmagick import Blob, Image, Geometry
from PyPDF3 import PdfFileReader, PdfFileWriter
from django.core.files.base import ContentFile


def generate_pdf_thumbnail(data, filename, page_number=0, height=800):
    # First, extract from the pdf doc the page we want a preview from
    pdf_source = PdfFileReader(data)
    pdf_temp = PdfFileWriter()
    page_buf = bytearray()

    page = pdf_source.getPage(page_number)
    pdf_temp.addPage(page)

    # Next, write the page into a temporary buffer, then render a thumbnail
    pdf_temp.write(page_buf)

    in_blob = Blob(page_buf)
    image = Image(in_blob)
    width = image.geometry.width / image.geometry.height * height
    image.zoom(Geometry(width, height))

    out_blob = Blob()
    image.write(out_blob)

    return ContentFile(out_blob.data, filename)
