from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.search import index
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render


class WebsiteNewsSearch(Page):
    max_count = 1
    copy = models.CharField(
        max_length=400,
        null=True,
        blank=True,
    )

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("copy"),
    ]

    def serve(self, request):
        search_query = request.GET.get("query", "")
        results = (
            WebsiteNewsPage.objects.live().search(search_query)
            if search_query
            else WebsiteNewsPage.objects.none()
        )

        return render(
            request,
            "website_news/news_search_results.html",
            {
                "search_query": search_query,
                "results": results,
                "copy": self.copy,
            },
        )


class WebsiteNewsIndexPage(Page):
    max_count = 1
    subtitle = models.CharField(max_length=200, blank=True, default="")

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = ["website_news.WebsiteNewsPage"]

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        all_news = WebsiteNewsPage.objects.live().order_by("-published_on")
        paginator = Paginator(all_news, 10)
        page = request.GET.get("page")
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        news_search = WebsiteNewsSearch.objects.first() or None
        if news_search:
            search_url = news_search.url
        else:
            search_url = "#"
        context["all_news"] = posts
        context["search_url"] = search_url
        return context


class WebsiteNewsPage(Page):
    copy = RichTextField()
    published_on = models.DateField()

    parent_page_types = ["website_news.WebsiteNewsIndexPage"]
    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("title"),
        index.SearchField("copy"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("copy"),
        FieldPanel("published_on"),
    ]
