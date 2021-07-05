from rest_framework import serializers
from taggit.models import Tag
from wagtail.documents.models import Document
from wagtail.search import queryset

from publications import models

COMMON_PAGE_FIELDS = ('id', 'title', 'tags', 'slug', 'parent')


class TagField(serializers.RelatedField):
    queryset = Tag.objects.all()

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        tag, _ = self.queryset.get_or_create(name=data)
        return tag


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'file', )


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Publication
        fields = COMMON_PAGE_FIELDS

    tags = TagField(many=True, allow_empty=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Page.objects.all())


class AbstractIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AbstractIssue
        fields = COMMON_PAGE_FIELDS + \
            ('publication_date', 'issue', 'volume', 'number')

    tags = TagField(many=True, allow_empty=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Page.objects.all())


class SimpleIssueSerializer(AbstractIssueSerializer):
    class Meta(AbstractIssueSerializer.Meta):
        model = models.SimpleIssue
        fields = AbstractIssueSerializer.Meta.fields + \
            ('issue_content',)


class MultiArticleIssueSerializer(AbstractIssueSerializer):
    class Meta(AbstractIssueSerializer.Meta):
        model = models.MultiArticleIssue
        fields = AbstractIssueSerializer.Meta.fields + \
            ('issue_cover',)


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Article
        fields = COMMON_PAGE_FIELDS + \
            ('article_content', 'author_name', 'intro_text')

    tags = TagField(many=True, allow_empty=True)
    article_content = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all())
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Page.objects.all())
