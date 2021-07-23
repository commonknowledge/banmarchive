from threading import Thread

from django.contrib import admin

from search import models
from publications.models import Article


@admin.register(models.AdvancedSearchIndex)
class GenericAdmin(admin.ModelAdmin):
    pass
