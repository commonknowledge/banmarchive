from datetime import date
from django.db import models
from django import forms
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index

from website_generic_page.models import PageWithHeroImageMixin


class WebsiteAwardsSearch(Page):
    max_count = 1

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = []

    def serve(self, request):
        search_query = request.GET.get("query", "")
        results = (
            WebsiteAwardPage.objects.live().search(search_query)
            if search_query
            else WebsiteAwardPage.objects.none()
        )

        paginator = Paginator(results, 10)
        page = request.GET.get("page")
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        index_page = WebsiteAwardsIndexPage.objects.first()

        return render(
            request,
            "website_awards/website_awards_index_page.html",
            {
                "page": index_page,
                "search_query": search_query,
                "posts": posts,
                "search_count": results.count(),
                "search_page": self,
            },
        )


class WebsiteAwardsIndexPage(PageWithHeroImageMixin):
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
        context["posts"] = posts
        context["search_page"] = awards_search
        return context


class WebsiteAwardPage(Page):
    parent_page_types = ["website_awards.WebsiteAwardsIndexPage"]
    subpage_types = []

    AWARD_TYPES = [
        ("standard", "Standard Award"),
        ("ninafishman", "Nina Fishman Translation Award"),
        ("major", "Major Award"),
    ]
    content = RichTextField(
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

    @property
    def hero_image(self):
        return self.get_parent().specific.hero_image

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
