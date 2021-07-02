from django.contrib import admin

from search import models


@admin.register(models.KeywordExtractor, models.AdvancedSearchIndex)
class GenericAdmin(admin.ModelAdmin):
    pass
