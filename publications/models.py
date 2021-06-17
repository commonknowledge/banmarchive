from random import randint

from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.documents.models import Document
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from taggit.models import TaggedItemBase

from helpers.content import get_children_of_type
from helpers.thumbnail_generator import PdfThumbnailMixin
from search.models import IndexedPdfMixin


class PageTag(TaggedItemBase):
    content_object = ParentalKey(
        Page,
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class AbstractArchiveItem(Page):
    class Meta:
        abstract = True

    @property
    def parent(self):
        return self.get_parent()


class Publication(AbstractArchiveItem):
    # Config
    parent_page_types = ('home.HomePage',)

    # Page fields
    tags = ClusterTaggableManager(through=PageTag, blank=True)
    introduction_content = RichTextField(blank=True, null=True)
    introduction_author = models.CharField(
        max_length=1024, blank=True, null=True)
    introduction_date = models.DateField(blank=True, null=True)

    # Data
    @property
    def issues(self):
        return get_children_of_type(self, SimpleIssue, MultiArticleIssue)

    @property
    def cover_image(self):
        image_count = self.issues.count()
        if image_count == 0:
            return None

        index = randint(0, image_count - 1)
        return self.issues[index].specific.cover_image


class AbstractIssue(PdfThumbnailMixin, AbstractArchiveItem):
    class Meta:
        abstract = True

    # Config
    parent_page_types = ('Publication',)

    search_fields = AbstractArchiveItem.search_fields + [
        index.FilterField('tags'),
        index.FilterField('publication_date'),
    ]

    promote_panels = AbstractArchiveItem.promote_panels + [
        ImageChooserPanel('cover_image')
    ]

    content_panels = AbstractArchiveItem.content_panels + (
        MultiFieldPanel(
            (
                FieldPanel('publication_date'),
                FieldPanel('issue'),
                FieldPanel('volume'),
                FieldPanel('number'),
            ),
            'Publication details'
        ),
    )

    # Page fields
    tags = ClusterTaggableManager(through=PageTag, blank=True)
    publication_date = models.DateField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    issue = models.IntegerField(blank=True, null=True)
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


class SimpleIssue(IndexedPdfMixin, AbstractIssue):
    # Config
    thumbnail_attribute = 'cover_image'

    content_panels = (DocumentChooserPanel('issue_content'),
                      FieldPanel('text_content'),) + \
        AbstractIssue.content_panels

    search_fields = AbstractIssue.search_fields + [
        index.SearchField('text_content'),
    ]

    pdf_text_mapping = {
        'issue_content': 'text_content'
    }

    def get_thumbnail_document(self):
        return self.issue_content

    # Page fields
    issue_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    text_content = models.TextField(blank=True, default='')

    # Data
    @property
    def pdf(self):
        return self.issue_content


class MultiArticleIssue(AbstractIssue):
    # Config
    thumbnail_attribute = 'cover_image'

    content_panels = (DocumentChooserPanel('issue_cover'),) + \
        AbstractIssue.content_panels

    def get_thumbnail_document(self):
        return self.issue_cover

    # Page fields
    issue_cover = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    # Data
    @property
    def articles(self):
        return get_children_of_type(self, Article)

    @property
    def pdf(self):
        return self.issue_cover


class Article(IndexedPdfMixin, PdfThumbnailMixin, AbstractArchiveItem):
    # Config
    thumbnail_attribute = 'page_image'

    pdf_text_mapping = {
        'article_content': 'text_content'
    }

    search_fields = AbstractArchiveItem.search_fields + [
        index.SearchField('text_content'),
        index.SearchField('author_name'),
        index.FilterField('tags'),
    ]

    template = 'publications/multi_article_issue.html'

    parent_page_types = ('MultiArticleIssue',)

    content_panels = AbstractArchiveItem.content_panels + [
        FieldPanel('author_name'),
        DocumentChooserPanel('article_content'),
        FieldPanel('tags'),
        FieldPanel('intro_text'),
        FieldPanel('text_content'),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    ]

    # Page fields
    author_name = models.CharField(max_length=1024, blank=True, null=True)
    intro_text = models.TextField(blank=True, null=True)
    article_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    tags = ClusterTaggableManager(
        through=PageTag, blank=True, verbose_name='Keywords')
    text_content = models.TextField(blank=True, default='')

    page_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    # Data
    @property
    def issue(self):
        return self.get_parent().specific

    @property
    def articles(self):
        return get_children_of_type(self.issue, Article)

    @property
    def pdf(self):
        return self.article_content
