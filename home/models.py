from helpers.cache import django_cached, django_cached_model
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core import blocks
from wagtail.core.models import Page, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.admin.edit_handlers import StreamFieldPanel
from django.db import models

from helpers.content import get_children_of_type, random_model
from publications.models import Publication, MultiArticleIssue, SimpleIssue


class ParagraphsBlock(blocks.StructBlock):
    content = blocks.RichTextBlock()
    side_images = blocks.ListBlock(ImageChooserBlock(), blank=True)

    class Meta:
        template = "home/blocks/paragraphs.html"
        icon = "rich_text"

    def get_context(self, value, *args, **kwargs):
        ctx = super().get_context(value, *args, **kwargs)
        ctx["side_images_with_links"] = self.side_images_with_links(
            value["side_images"]
        )

        return ctx

    def side_images_with_links(self, images):
        # @django_cached_model('home.models.ParagraphsBlock.side_images_with_links.get_issue')
        def get_issue(img):
            return (
                MultiArticleIssue.objects.filter(cover_image=img).first()
                or SimpleIssue.objects.filter(cover_image=img).first()
            )

        return ({"img": img, "issue": get_issue(img)} for img in images)


class HomePage(Page):
    parent_page_types = ()

    @property
    def publications(self):
        return get_children_of_type(self, Publication)

    @property
    def issue_sample(self):
        return (
            p.random_issue()
            for p in random_model(
                self.publications.live().filter(numchild__gt=0), count=4
            )
        )


class ArticlePage(Page):
    author = models.CharField(max_length=1024, blank=True, default="")
    author_role = models.CharField(max_length=1024, blank=True, default="")
    date = models.DateField(null=True, blank=True)
    content = StreamField(
        (
            ("paragraph", ParagraphsBlock()),
            ("pull_quote", blocks.TextBlock(template="home/blocks/pull_quote.html")),
        )
    )

    def displayed_title(self):
        try:
            if self.introduction_for_publication is not None:
                return self.introduction_for_publication.title
        except:
            pass

        return self.title

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            (
                FieldPanel("author"),
                FieldPanel("author_role"),
            ),
            "Author",
        ),
        FieldPanel("date"),
        StreamFieldPanel("content"),
    ]
