from django.shortcuts import render
from wagtail.search.models import Query
from .models import WebsiteNewsPage


def news_search(request):
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
        },
    )
