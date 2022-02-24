from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail_transfer import urls as wagtailtransfer_urls

from banmarchive import views
from search import views as search_views
from helpers import rest


urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),

    path('404/', views.handler404),
    path('search/', search_views.search, name='search'),
    path('api/', include(rest.get_urls())),
]


if settings.DEBUG:
    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    re_path(r'^wagtail-transfer/', include(wagtailtransfer_urls)),
    path("", include(wagtail_urls)),
]

handler404 = 'banmarchive.views.handler404'
