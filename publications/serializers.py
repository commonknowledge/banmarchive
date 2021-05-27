from rest_framework import serializers
from publications import models

COMMON_PAGE_FIELDS = ('id', 'title', 'slug', 'tags', 'parent')


class PageTagField(serializers.RelatedField):
    queryset = models.PageTag.objects.all()

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        tag, _ = self.queryset.get_or_create(name=data)
        return tag


class AbstractIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AbstractIssue
        fields = COMMON_PAGE_FIELDS + ('publication_date',)

    tags = PageTagField(many=True)


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Article
        fields = COMMON_PAGE_FIELDS + ('article_content',)

    tags = PageTagField(many=True)
    article_content = serializers.FileField()
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Article.objects.all())


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Publication
        fields = COMMON_PAGE_FIELDS + \
            ('introduction_content', 'introduction_author', 'introduction_date')

    tags = PageTagField(many=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Page.objects.all())


class SimpleIssueSerializer(AbstractIssueSerializer):
    class Meta(AbstractIssueSerializer.Meta):
        fields = AbstractIssueSerializer.Meta.fields + \
            ('issue_content',)

    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Page.objects.all())
    issue_content = serializers.FileField()


class MultiArticleIssueSerializer(AbstractIssueSerializer):
    class Meta(AbstractIssueSerializer.Meta):
        fields = AbstractIssueSerializer.Meta.fields + \
            ('articles',)

    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.Page.objects.all())
    articles = ArticleSerializer(many=True)
