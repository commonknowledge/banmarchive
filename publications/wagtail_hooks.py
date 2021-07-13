from django.urls.base import reverse
from wagtail.core import hooks
from wagtail.admin.menu import MenuItem
from django.urls import path

from publications import views


@hooks.register('register_admin_menu_item')
def register_import_menu():
    return MenuItem('Upload Content', reverse('bulk_upload_admin'), icon_name='doc-empty-inverse', order=10000)


@hooks.register('register_admin_urls')
def urlconf_bulk_upload():
    return [
        path('upload/', views.ArticlesMissingContentView.as_view(),
             name='bulk_upload_admin'),
        path('reports/incomplete-articles/',
             views.ArticlesMissingContentView.as_view(), name='incomplete_articles'),
        path('reports/incomplete-issues/',
             views.IssuesMissingContentView.as_view(), name='incomplete_issues'),
    ]


@hooks.register('register_reports_menu_item')
def register_unpublished_changes_report_menu_item():
    return MenuItem(
        "Incomplete Articles",
        reverse('incomplete_articles'),
        classnames='icon icon-' + views.ArticlesMissingContentView.header_icon, order=700)


@hooks.register('register_reports_menu_item')
def register_unpublished_changes_report_menu_item():
    return MenuItem(
        "Incomplete Issues",
        reverse('incomplete_issues'),
        classnames='icon icon-' + views.IssuesMissingContentView.header_icon, order=701)
