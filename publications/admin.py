from django.contrib import admin

from publications import models


@admin.register(models.SimpleIssue, models.MultiArticleIssue, models.Article, models.Publication)
class GenericAdmin(admin.ModelAdmin):
    pass
