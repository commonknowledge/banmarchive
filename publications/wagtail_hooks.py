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
        path('upload/',
             views.ImportView.as_view(), name='bulk_upload_admin'),
    ]
