from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core import blocks
from wagtail.core.models import Page, StreamField
from wagtail.images.blocks import ImageChooserBlock
from django.db import models

from helpers.content import get_children_of_type, random_model
from publications.models import Publication


class ParagraphsBlock(blocks.StructBlock):
    content = blocks.RichTextBlock()
    side_images = blocks.ListBlock(ImageChooserBlock())

    class Meta:
        template = 'home/blocks/paragraphs.html'
        icon = 'rich_text'


class HomePage(Page):
    parent_page_types = ()

    @property
    def publications(self):
        return get_children_of_type(self, Publication)

    @property
    def issue_sample(self):
        return (
            p.random_issue
            for p in random_model(self.publications, count=4)
        )


class ArticlePage(Page):
    author = models.CharField(max_length=1024, blank=True, default='')
    author_role = models.CharField(max_length=1024, blank=True, default='')
    date = models.DateField(null=True, blank=True)
    content = StreamField((
        ('paragraph', ParagraphsBlock()),
        ('pull_quote', blocks.TextBlock(template='home/blocks/pull_quote.html')),
    ))

    def displayed_title(self):
        if self.introduction_for_publication is not None:
            return self.introduction_for_publication.title

        return self.title

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            (
                FieldPanel('author'),
                FieldPanel('author_role'),
            ),
            'Author'
        ),
        FieldPanel('date'),
        FieldPanel('content')
    ]
