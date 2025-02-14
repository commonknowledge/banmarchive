from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField


class WebsiteAboutIndexPage(Page):
    max_count = 1
    subtitle = models.CharField(
        max_length=100, default="About The Barry Amiel & Norman Melburn Trust"
    )
    copy = RichTextField()

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = ["website_about.WebsiteAboutSectionPage"]

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("copy"),
    ]

    def get_about_subpages(self):
        return self.get_children().live()


class WebsiteAboutSectionPage(Page):
    copy = RichTextField()

    parent_page_types = ["website_about.WebsiteAboutIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("copy"),
    ]
