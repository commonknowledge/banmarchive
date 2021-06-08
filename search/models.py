from django.utils import text
import pdftotext

IndexedPdfMixinSubclasses = []


class IndexedPdfMixin:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        IndexedPdfMixinSubclasses.append(cls)

    pdf_text_mapping = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._indexed_pdf_mixin_init = dict({
            key: getattr(self, key).file
            for key in self.pdf_text_mapping.keys()
            if getattr(self, key) is not None
        })

    def save(self, clean=True, user=None, log_action=False, reindex_pdfs=True, **kwargs):
        if reindex_pdfs:
            for document_key, prev_document_file in self._indexed_pdf_mixin_init.items():
                # If it has changed, re-index the file.
                document = getattr(self, document_key)
                document_file = None if document is None else document.file

                if document_file != prev_document_file:
                    self.reindex_pdf_content(document_key, save=False)

        return super().save(clean=clean, user=user, log_action=log_action, **kwargs)

    def has_indexed_pdf_content(self):
        for document_key, text_content_key in self.pdf_text_mapping.items():
            text = getattr(self, text_content_key)
            if getattr(self, document_key) is not None and text is None or text == '':
                return False

        return True

    def reindex_pdf_content(self, document_key: str = None, save=True):
        if document_key is None:
            for document_key in self.pdf_text_mapping.keys():
                self.reindex_pdf_content(document_key, save=False)

        else:
            document_value = getattr(self, document_key, None)
            text_content_key = self.pdf_text_mapping[document_key]

            # No document associated, set the text content to empty
            if document_value is None or document_value.file is None:
                setattr(self, text_content_key, '')
                return

            # Pdf document associated, extract text from the pdf and save it to the database
            with document_value.file.storage.open(document_value.file.name, 'rb') as fd:
                pdf = pdftotext.PDF(fd)
                text_content = "\n\n".join(pdf)

            setattr(self, text_content_key, text_content)

        if save:
            self.save(reindex_pdfs=False)
