from wagtail.core.models import Page
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import post_save
from django.utils import text
from django.db import models
import pdftotext

IndexedPdfMixinSubclasses = []


class IndexedPdfMixin:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        IndexedPdfMixinSubclasses.append(cls)

    '''
    Mapping of pdf document attributes to text attributes that should hold the document content.
    '''
    pdf_text_mapping = {}

    def save(self, *args, reindex_pdfs=True, **kwargs):
        '''
        Intercept save of model and reindex the pdf if it doesn't have any searchable content
        '''

        if reindex_pdfs:
            for document_key in self.pdf_text_mapping.keys():
                if not self.has_indexed_pdf_content(document_key):
                    self.reindex_pdf_content(document_key, save=False)

        return super().save(*args, **kwargs)

    def has_indexed_pdf_content(self, document_key=None):
        '''
        True if all of this model's pdf documents have been indexed.
        '''

        if document_key is not None:
            text_content_key = self.pdf_text_mapping[document_key]
            text = getattr(self, text_content_key)

            return getattr(self, document_key) is not None and text is not None and text != ''

        for document_key in self.pdf_text_mapping.keys():
            if not self.has_indexed_pdf_content(document_key):
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


class AdvancedSearchIndex(models.Model):
    class Meta:
        indexes = (
            GinIndex(fields=['keywords']),
        )

    page_id = models.ForeignKey(Page, on_delete=models.CASCADE)
    keywords = models.JSONField(default=list)

    @staticmethod
    def index(article):
        keywords = []
        article = article.specific

        def add_kw(ns, src, transform=lambda x: x):
            if src is not None:
                keywords.append((ns, transform(src)))

        add_kw('decade', article.issue.publication_date,
               lambda date: int(date.year / 10) * 10)
        add_kw('author', article.author_name)
        add_kw('publication', article.publication.id)

        for tag in article.tags.all():
            keywords.append(tag.name)

        index, created = AdvancedSearchIndex.objects.get_or_create(
            page_id=article,
            defaults={'keywords': keywords}
        )
        if created is False:
            index.keywords = keywords
            index.save()

        return index

    @staticmethod
    def _handle_post_save(sender, instance, **kwargs):
        from publications.models import Article, MultiArticleIssue

        if sender == Article:
            AdvancedSearchIndex.index(instance)
        elif sender == MultiArticleIssue:
            for article in instance.articles:
                AdvancedSearchIndex.index(article)
