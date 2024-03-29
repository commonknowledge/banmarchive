from helpers.cache import django_cached
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponseRedirect
from django.db.models.fields import related
from django.db.models.signals import post_save, pre_save
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.documents.models import Document
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from wagtail.search import index
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from taggit.models import TaggedItemBase

from helpers.content import get_children_of_type, get_page, random_model
from helpers.thumbnail_generator import PdfThumbnailMixin
from search.models import AdvancedSearchIndex, IndexedPdfMixin, extract_keywords


class ArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        'publications.Article',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class SimpleIssueTag(TaggedItemBase):
    content_object = ParentalKey(
        'publications.SimpleIssue',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class AbstractArchiveItem(Page):
    class Meta:
        abstract = True

    @property
    def parent(self):
        return self.get_parent().specific


class Publication(AbstractArchiveItem):
    # Config
    parent_page_types = ('home.HomePage',)

    content_panels = AbstractArchiveItem.content_panels + [
        FieldPanel('short_introduction'),
        PageChooserPanel('introduction_article'),
    ]

    # Page fields
    short_introduction = RichTextField(blank=True)
    introduction_article = models.OneToOneField(
        'home.ArticlePage', blank=True, null=True, related_name='introduction_for_publication', on_delete=models.SET_NULL)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        paginator = Paginator(self.issues, 20)
        page = get_page(request)
        context['issues'] = paginator.get_page(page)
        context['paginator'] = paginator
        context['years'] = self.years()

        return context

    # Data
    is_publication = True

    @property
    def issues(self):
        return get_children_of_type(self, SimpleIssue, MultiArticleIssue)

    @django_cached('publications.models.Publication.years', lambda self: self.id)
    def years(self):
        def cmp_if_not_none(a, b, cmp):
            if a is None:
                return b
            if b is None:
                return a

            return cmp(a, b)

        min_simple = get_children_of_type(self, SimpleIssue).aggregate(
            models.Min('publication_date'))['publication_date__min']
        max_simple = get_children_of_type(self, SimpleIssue).aggregate(
            models.Max('publication_date'))['publication_date__max']
        min_multi = get_children_of_type(self, MultiArticleIssue).aggregate(
            models.Min('publication_date'))['publication_date__min']
        max_multi = get_children_of_type(self, MultiArticleIssue).aggregate(
            models.Max('publication_date'))['publication_date__max']

        earliest = cmp_if_not_none(min_simple, min_multi, min)
        latest = cmp_if_not_none(max_simple, max_multi, max)

        if not earliest or not latest:
            return None

        return range(earliest.year, latest.year + 1)

    @django_cached('publications.models.Publication.num_issues', lambda self: self.id)
    def num_issues(self):
        return self.issues.count()

    def year_range_str(self):
        years = self.years()

        if years is None:
            return ''

        return f'{years.start}–{years.stop - 1}'

    @django_cached('publications.models.Publication.random_issue', lambda self: self.id)
    def random_issue(self):
        for _ in range(5):
            candidate = random_model(self.issues.live())
            if candidate is not None and candidate.specific.get_thumbnail_document() is not None:
                return candidate

        return candidate

    @property
    def search_meta_info(self):
        return self.title


class AbstractIssue(PdfThumbnailMixin, AbstractArchiveItem):
    class Meta:
        abstract = True

    shows_contents = False

    # Config
    parent_page_types = ('Publication',)

    search_fields = AbstractArchiveItem.search_fields + [
        index.FilterField('publication_date'),
    ]

    promote_panels = AbstractArchiveItem.promote_panels + [
        ImageChooserPanel('cover_image')
    ]

    content_panels = AbstractArchiveItem.content_panels + [
        MultiFieldPanel(
            (
                FieldPanel('publication_date'),
                FieldPanel('issue'),
                FieldPanel('volume'),
                FieldPanel('number'),
            ),
            'Publication details'
        )
    ]

    @property
    def issue_page(self):
        return self

    @property
    def publication(self):
        return self.parent

    @property
    def search_meta_info(self):
        return f'{self.publication.title} {self.issue_page.title}'

    # Page fields
    publication_date = models.DateField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    issue = models.IntegerField(blank=True, null=True)
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


class SimpleIssue(IndexedPdfMixin, AbstractIssue):
    # Config
    thumbnail_attribute = 'cover_image'

    content_panels = [
        DocumentChooserPanel('issue_content'),
        FieldPanel('text_content'),
        FieldPanel('tags'),
        FieldPanel(
            'author_name', help_text='Names of authors of articles in this issue, separated using commas'),
    ] + AbstractIssue.content_panels

    search_fields = AbstractIssue.search_fields + [
        index.SearchField('text_content'),
    ]

    template = 'publications/issue.html'

    pdf_text_mapping = {
        'issue_content': 'text_content'
    }

    author_name = models.TextField(
        verbose_name='Author Names', blank=True, default='')

    def get_thumbnail_document(self):
        return self.issue_content

    # Page fields
    issue_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    text_content = models.TextField(blank=True, default='')

    tags = ClusterTaggableManager(
        through=SimpleIssueTag, blank=True, verbose_name='Keywords')

    # Data
    @property
    def pdf(self):
        return self.issue_content

    @property
    def search_meta_info(self):
        return f'{self.publication.title}'

    def save(self, *args, generate_keywords=True, **kwargs):
        if generate_keywords:
            extract_keywords((self, ))

        super().save(*args, **kwargs)


class MultiArticleIssue(AbstractIssue):
    # Config
    thumbnail_attribute = 'cover_image'

    template = 'publications/issue.html'

    @property
    def shows_contents(self):
        return get_children_of_type(self, Article).count() > 0

    content_panels = [DocumentChooserPanel('issue_cover')] + \
        AbstractIssue.content_panels

    def get_thumbnail_document(self):
        return self.pdf

    # Page fields
    issue_cover = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Data
    @property
    def articles(self):
        return get_children_of_type(self, Article)

    @property
    def pdf(self):
        if self.issue_cover is None:
            article = self.articles.first()
            return article.pdf if article is not None else None

        return self.issue_cover

    def serve(self, request, *args, **kwargs):
        if self.issue_cover is None:
            article = self.articles.first()

            if article is not None:
                return HttpResponseRedirect(article.url)

        return super().serve(request, *args, **kwargs)


class Article(IndexedPdfMixin, PdfThumbnailMixin, AbstractArchiveItem):
    # Config
    thumbnail_attribute = 'page_image'

    @property
    def shows_contents(self):
        return get_children_of_type(self.get_parent(), Article).count() > 0

    pdf_text_mapping = {
        'article_content': 'text_content'
    }

    search_fields = AbstractArchiveItem.search_fields + [
        index.SearchField('text_content'),
        index.SearchField('author_name'),
    ]

    template = 'publications/issue.html'

    parent_page_types = ('MultiArticleIssue',)

    content_panels = AbstractArchiveItem.content_panels + [
        FieldPanel(
            'author_name', help_text='Name of the article author. If multiple authors, separate them using commas'),
        DocumentChooserPanel('article_content'),
        FieldPanel('tags'),
        FieldPanel('summary'),
        FieldPanel('text_content'),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    ]

    # Page fields
    author_name = models.CharField(max_length=1024, blank=True, null=True)
    article_content = models.ForeignKey(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    tags = ClusterTaggableManager(
        through=ArticleTag, blank=True, verbose_name='Keywords')
    text_content = models.TextField(blank=True, default='')

    page_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    # Data
    @property
    def issue(self) -> MultiArticleIssue:
        return self.parent

    @property
    def issue_page(self):
        return self.issue

    @property
    def publication(self) -> Publication:
        return self.issue_page.parent

    @property
    def articles(self):
        return get_children_of_type(self.issue, Article)

    @property
    def pdf(self):
        return self.article_content

    @property
    def search_meta_info(self):
        return f'{self.publication.title} {self.issue.title}'

    def save(self, *args, generate_keywords=True, **kwargs):
        if generate_keywords:
            extract_keywords((self, ))

        super().save(*args, **kwargs)


post_save.connect(AdvancedSearchIndex._handle_post_save, sender=Article)
post_save.connect(AdvancedSearchIndex._handle_post_save, sender=SimpleIssue)
post_save.connect(AdvancedSearchIndex._handle_post_save,
                  sender=MultiArticleIssue)
