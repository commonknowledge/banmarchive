from datetime import date
from django.db import models
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.search import index


class WebsiteAwardsSearch(Page):
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
            WebsiteAwardPage.objects.live().search(search_query)
            if search_query
            else WebsiteAwardPage.objects.none()
        )

        return render(
            request,
            "website_awards/awards_search_results.html",
            {
                "search_query": search_query,
                "results": results,
                "copy": self.copy,
            },
        )


class WebsiteAwardsIndexPage(Page):
    max_count = 1

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = ["website_awards.WebsiteAwardPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        all_awards = (
            WebsiteAwardPage.objects.all()
            .live()
            .order_by(models.F("year").desc(nulls_last=True), "title")
        )
        paginator = Paginator(all_awards, 10)
        page = request.GET.get("page")
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        awards_search = WebsiteAwardsSearch.objects.first() or None
        if awards_search:
            search_url = awards_search.url
        else:
            search_url = "#"
        context["posts"] = posts
        context["search_url"] = search_url
        return context


class WebsiteAwardPage(Page):
    parent_page_types = ["website_awards.WebsiteAwardsIndexPage"]
    subpage_types = []

    AWARD_TYPES = [
        ("standard", "Standard Award"),
        ("ninafishman", "Nina Fishman Translation Award"),
        ("major", "Major Award"),
    ]
    content = models.TextField(
        null=True,
        blank=True,
    )
    post_date = models.DateField(default=date.today)
    organisation = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    year = models.CharField(
        max_length=12, null=True, blank=True, verbose_name="Year awarded"
    )
    amount_awarded = models.FloatField(
        null=True,
        blank=True,
    )
    website = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    award_type = models.CharField(
        max_length=40,
        choices=AWARD_TYPES,
        null=True,
        blank=True,
    )

    search_fields = Page.search_fields + [
        index.SearchField("title"),
        index.SearchField("content"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel(
            "content",
            widget=forms.Textarea(attrs={"rows": 10, "cols": 80}),
        ),
        FieldPanel("organisation"),
        FieldPanel("year"),
        FieldPanel("amount_awarded"),
        FieldPanel("website"),
        FieldPanel("award_type"),
        FieldPanel("post_date"),
    ]
