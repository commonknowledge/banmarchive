from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField


class WebsiteGenericPage(Page):
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    copy = RichTextField()

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("copy"),
    ]
