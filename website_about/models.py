from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField

from website_generic_page.models import PageWithHeroImageMixin


class WebsiteAboutIndexPage(PageWithHeroImageMixin):
    max_count = 1
    subtitle = models.CharField(
        max_length=100, default="About The Barry Amiel & Norman Melburn Trust"
    )
    copy = RichTextField()

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = ["website_about.WebsiteAboutSectionPage"]

    content_panels = PageWithHeroImageMixin.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("copy"),
    ]

    def get_about_subpages(self):
        return self.get_children().live()


class WebsiteAboutSectionPage(PageWithHeroImageMixin):
    copy = RichTextField()
    subtitle = models.CharField(max_length=100, blank=True, null=True)
    parent_page_types = ["website_about.WebsiteAboutIndexPage"]
    subpage_types = []

    content_panels = PageWithHeroImageMixin.content_panels + [
        FieldPanel("copy"),
    ]
