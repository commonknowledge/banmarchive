from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.fields import RichTextField


class PageWithHeroImageMixin(Page):
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel("hero_image"),
    ]

    class Meta:
        abstract = True


class WebsiteGenericPage(PageWithHeroImageMixin):
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    copy = RichTextField()

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = []

    content_panels = PageWithHeroImageMixin.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("copy"),
    ]
