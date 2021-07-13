from threading import Thread

from django.contrib import admin

from search import models
from publications.models import Article


@admin.register(models.AdvancedSearchIndex)
class GenericAdmin(admin.ModelAdmin):
    pass


@admin.register(models.KeywordExtractor)
class GenericAdmin(admin.ModelAdmin):
    actions = ['retrain', 'regenerate']

    @staticmethod
    def _retrain(queryset, *args, **kwargs):
        for extractor in queryset:
            extractor.train_model(Article.objects.all())

    @admin.action(description='Retrain keyword extraction models')
    def retrain(self, request, queryset):
        Thread(target=GenericAdmin._retrain, args=(queryset,)).start()

    @staticmethod
    def _regenerate(queryset, *args, **kwargs):
        for extractor in queryset:
            extractor.fit_keywords(Article.objects.all())

    @admin.action(description='Regenerate all keywords')
    def regenerate(self, request, queryset):
        Thread(target=GenericAdmin._regenerate, args=(queryset,)).start()
