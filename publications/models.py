from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.documents.models import Document
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

    # Page fields
    tags = ClusterTaggableManager(through=PageTag, blank=True)
    publication_date = models.DateField(blank=True, null=True)


class SimpleIssue(AbstractIssue):
    issue_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


class MultiArticleIssue(AbstractIssue):
    issue_cover = RichTextField(blank=True, null=True)


class Article(AbstractArchiveItem):
    # Config
    parent_page_types = ('MultiArticleIssue',)

    # Page fields
    article_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    tags = ClusterTaggableManager(through=PageTag, blank=True)
