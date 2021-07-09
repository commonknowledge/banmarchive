from django.contrib import admin

from search import models
from publications.models import Article


@admin.register(models.AdvancedSearchIndex)
class GenericAdmin(admin.ModelAdmin):
    pass


@admin.register(models.KeywordExtractor)
class GenericAdmin(admin.ModelAdmin):
    actions = ['retrain', 'regenerate']

    @admin.action(description='Retrain keyword extraction models')
    def retrain(self, request, queryset):
        for extractor in queryset:
            extractor.train_model(Article.objects.all())

    @admin.action(description='Regenerate all keywords')
    def regenerate(self, request, queryset):
        for extractor in queryset:
            extractor.fit_keywords(Article.objects.all())
