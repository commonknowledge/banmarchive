from django import template
from website_home.models import WebsiteHomePage
from website_about.models import WebsiteAboutIndexPage
from website_awards.models import WebsiteAwardsIndexPage
from website_events.models import WebsiteEventIndexPage
from website_news.models import WebsiteNewsIndexPage


register = template.Library()


@register.simple_tag
def get_navigation_pages():
    """Retrieve all index page models for navigation."""

    about_page = WebsiteAboutIndexPage.objects.first()

    about_children = about_page.get_about_subpages() if about_page else []

    return [
        {
            "title": "Home",
            "url": (
                WebsiteHomePage.objects.first().url
                if WebsiteHomePage.objects.exists()
                else "#"
            ),
        },
        {
            "title": "About",
            "url": about_page.url if about_page else "#",
            "children": [
                {"title": child.title, "url": child.url} for child in about_children
            ],
        },
        {
            "title": "News",
            "url": (
                WebsiteNewsIndexPage.objects.first().url
                if WebsiteNewsIndexPage.objects.exists()
                else "#"
            ),
        },
        {
            "title": "Awards",
            "url": (
                WebsiteAwardsIndexPage.objects.first().url
                if WebsiteAwardsIndexPage.objects.exists()
                else "#"
            ),
        },
    ]
