from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.documents.models import Document
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.documents.edit_handlers import DocumentChooserPanel
from taggit.models import TaggedItemBase


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


class AbstractIssue(AbstractArchiveItem):
    class Meta:
        abstract = True

    # Config
    parent_page_types = ('Publication',)

    content_panels = (
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


class SimpleIssue(AbstractIssue):
    # Config
    content_panels = (DocumentChooserPanel('issue_content'),) + \
        AbstractIssue.content_panels

    # Page fields
    issue_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


class MultiArticleIssue(AbstractIssue):
    # Config
    content_panels = (DocumentChooserPanel('issue_cover'),) + \
        AbstractIssue.content_panels

    # Page fields
    issue_cover = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


class Article(AbstractArchiveItem):
    # Config
    parent_page_types = ('MultiArticleIssue',)

    content_panels = Page.content_panels + [
        FieldPanel('author_name'),
        DocumentChooserPanel('article_content'),
        FieldPanel('tags'),
        FieldPanel('intro_text'),
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
