from django.db import models
from django import forms
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from .blocks import HomePageTeaserBlock

from website_about.models import WebsiteAboutIndexPage
from website_generic_page.models import PageWithHeroImageMixin


class WebsiteHomePage(PageWithHeroImageMixin):
    max_count = 1
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        default="What is the Barry Amiel & Norman Melburn trust?",
    )
    copy = RichTextField(
        default="The Trust was founded \
in 1980 by Norman Melburn and named for his friend and \
fellow Marxist, the lawyer Barry Amiel. Since Norman Melburn’s \
death in 1991, both men have been commemorated in the name of the Trust.\n\
The general objectives of the Trust are to advance public education, \
learning and knowledge in all aspects of the philosophy of Marxism, \
the history of socialism, and the working class movement. \
The Trust, as well as initiating activity or research in pursuit of \
these objects, is open to applications for funding.\n\
The Trust will give financial assistance to bodies or individuals \
for projects which it considers fall within the scope \
of the Trust’s remit."
    )

    teasers = StreamField(
        [
            ("teaser", HomePageTeaserBlock()),
        ],
        blank=True,
        max_num=4,
    )

    def get_about_page(self):
        about_page = WebsiteAboutIndexPage.objects.all().first()
        if about_page:
            return about_page
        return None

    subpage_types = [
        "website_news.WebsiteNewsIndexPage",
        "website_news.WebsiteNewsPage",
        "website_about.WebsiteAboutIndexPage",
        "website_awards.WebsiteAwardsIndexPage",
        "website_news.WebsiteNewsSearch",
        "website_awards.WebsiteAwardsSearch",
        "website_generic_page.WebsiteGenericPage",
    ]

    content_panels = PageWithHeroImageMixin.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel(
            "copy",
            help_text="Enter detailed content here.",
        ),
        StreamFieldPanel("teasers"),
    ]
