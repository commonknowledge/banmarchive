import logging
import string
import re
from itertools import zip_longest
from nltk.sem.evaluate import Error

import spacy
from nltk import tokenize
from taggit.models import Tag
from wagtail.core.models import Page
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import post_save
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
                self.reindex_pdf_content(document_key, save=save)

        else:
            try:
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
            except Exception as ex:
                logging.error(ex)


class AdvancedSearchIndex(models.Model):
    class Meta:
        indexes = (
            GinIndex(fields=['keywords']),
            models.indexes.Index(fields=['page_id'])
        )

    page_id = models.ForeignKey(Page, on_delete=models.CASCADE)
    keywords = models.JSONField(default=list)

    def __str__(self):
        return str(self.page_id)

    @staticmethod
    def index(article):
        keywords = []
        article = article.specific

        def add_kw(ns, src, transform=lambda x: x):
            if src is not None:
                val = transform(src)
                if isinstance(val, str):
                    val = val.lower()

                keywords.append((ns, val))

        add_kw('decade', article.issue_page.publication_date,
               lambda date: int(date.year / 10) * 10)

        if article.author_name:
            for author in article.author_name.split(','):
                add_kw('author', author.strip())
                for part in author.split(' '):
                    add_kw('author', part.strip())

        add_kw('publication', article.publication.id)

        for tag in article.tags.all():
            keywords.append(tag.name.lower())

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
        from publications.models import Article, MultiArticleIssue, SimpleIssue

        if sender == Article:
            AdvancedSearchIndex.index(instance)
        elif sender == MultiArticleIssue:
            for article in instance.articles:
                AdvancedSearchIndex.index(article)
        elif sender == SimpleIssue:
            AdvancedSearchIndex.index(instance)


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def get_nlp():
    if not hasattr(get_nlp, '_nlp'):
        get_nlp._nlp = spacy.load('en_core_web_md')
    return get_nlp._nlp


def extract_keywords(qs):
    def get_tag(ent):
        tag, _ = Tag.objects.get_or_create(name=str(str(ent)))
        return tag

    for article in qs:
        if article.tags.exists():
            continue
        nlp = get_nlp()

        cleaned_text = "".join([
            i.lower()
            for i in article.text_content
            if i or i not in string.punctuation
        ])
        cleaned_text = ' '.join(
            i for i
            in tokenize.word_tokenize(cleaned_text)
            if not re.match(r'^\d+$', i)
        )

        ents = [
            get_tag(ent)
            for ent in nlp(cleaned_text).ents
            if len(str(ent)) < 100
            and len(str(ent)) > 2
        ]

        article.tags.add(*ents)
        article.save(generate_keywords=False)
