from django.shortcuts import render
from wagtail.search.models import Query
from .models import WebsiteAwardPage


def awards_search(request):
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
        },
    )
