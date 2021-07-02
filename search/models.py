from itertools import zip_longest
import pickle
import re
from nltk.stem.wordnet import WordNetLemmatizer

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from wagtail.core.models import Page
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import post_save
from django.utils import text
from django.db import models
from nltk import corpus
import pdftotext

IndexedPdfMixinSubclasses = []


class IndexedPdfMixin:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        IndexedPdfMixinSubclasses.append(cls)

    '''
    Mapping of pdf document attributes to text attributes that should hold the document content.
    '''
    pdf_text_mapping = {}

    def save(self, *args, reindex_pdfs=True, **kwargs):
        '''
        Intercept save of model and reindex the pdf if it doesn't have any searchable content
        '''

        if reindex_pdfs:
            for document_key in self.pdf_text_mapping.keys():
                if not self.has_indexed_pdf_content(document_key):
                    self.reindex_pdf_content(document_key, save=False)

        return super().save(*args, **kwargs)

    def has_indexed_pdf_content(self, document_key=None):
        '''
        True if all of this model's pdf documents have been indexed.
        '''

        if document_key is not None:
            text_content_key = self.pdf_text_mapping[document_key]
            text = getattr(self, text_content_key)

            return getattr(self, document_key) is not None and text is not None and text != ''

        for document_key in self.pdf_text_mapping.keys():
            if not self.has_indexed_pdf_content(document_key):
                return False

        return True

    def reindex_pdf_content(self, document_key: str = None, save=True):
        if document_key is None:
            for document_key in self.pdf_text_mapping.keys():
                self.reindex_pdf_content(document_key, save=False)

        else:
            document_value = getattr(self, document_key, None)
            text_content_key = self.pdf_text_mapping[document_key]

            # No document associated, set the text content to empty
            if document_value is None or document_value.file is None:
                setattr(self, text_content_key, '')
                return

            # Pdf document associated, extract text from the pdf and save it to the database
            with document_value.file.storage.open(document_value.file.name, 'rb') as fd:
                pdf = pdftotext.PDF(fd)
                text_content = "\n\n".join(pdf)

            setattr(self, text_content_key, text_content)

        if save:
            self.save(reindex_pdfs=False)


class AdvancedSearchIndex(models.Model):
    class Meta:
        indexes = (
            GinIndex(fields=['keywords']),
        )

    page_id = models.ForeignKey(Page, on_delete=models.CASCADE)
    keywords = models.JSONField(default=list)

    @staticmethod
    def index(article):
        keywords = []
        article = article.specific

        def add_kw(ns, src, transform=lambda x: x):
            if src is not None:
                keywords.append((ns, transform(src)))

        add_kw('decade', article.issue.publication_date,
               lambda date: int(date.year / 10) * 10)
        add_kw('author', article.author_name)
        add_kw('publication', article.publication.id)

        for tag in article.tags.all():
            keywords.append(tag.name)

        index, created = AdvancedSearchIndex.objects.get_or_create(
            page_id=article,
            defaults={'keywords': keywords}
        )
        if created is False:
            index.keywords = keywords
            index.save()

        return index

    @staticmethod
    def _handle_post_save(sender, instance, **kwargs):
        from publications.models import Article, MultiArticleIssue

        if sender == Article:
            AdvancedSearchIndex.index(instance)
        elif sender == MultiArticleIssue:
            for article in instance.articles:
                AdvancedSearchIndex.index(article)


class KeywordExtractor(models.Model):
    slug = models.SlugField(unique=True)
    tfidf_transformer = models.BinaryField(null=True, blank=True)
    cv = models.BinaryField(null=True, blank=True)
    stopwords = models.JSONField(default=list)
    keywords = models.JSONField(default=list)

    def __str__(self):
        return self.slug

    @staticmethod
    def article_extractor():
        extractor, _ = KeywordExtractor.objects.get_or_create(
            slug='article-keyword-extract')
        return extractor

    def pre_process(self, text, stopwords):
        # lowercase
        text = text.lower()

        # remove tags
        text = re.sub("&lt;/?.*?&gt;", " &lt;&gt; ", text)

        # remove special characters and digits
        text = re.sub("(\\d|\\W)+", " ", text)

        # Convert to list from string
        text = text.split()

        # remove stopwords
        text = [word for word in text if word not in stopwords]

        # remove words less than three letters
        text = [word for word in text if len(word) >= 3]

        # lemmatize
        lmtzr = WordNetLemmatizer()
        text = [lmtzr.lemmatize(word) for word in text]

        return ' '.join(text)

    def get_stopwords(self):
        stopwords = set(corpus.stopwords.words('english'))
        stopwords.update(self.stopwords)

        return stopwords

    @property
    def is_trained(self):
        return self.tfidf_transformer is not None and self.cv is not None

    def train_model(self, qs):
        stopwords = self.get_stopwords()
        all_articles = qs.iterator()
        tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
        cv = CountVectorizer(max_df=0.95,         # ignore words that appear in 95% of documents
                             max_features=10000,  # the size of the vocabulary
                             # vocabulary contains single words, bigrams, trigrams
                             ngram_range=(1, 3)
                             )

        docs = [self.pre_process(d.text_content, stopwords)
                for d in all_articles]

        word_count_vector = cv.fit_transform(docs)
        tfidf_transformer.fit(word_count_vector)

        self.tfidf_transformer = pickle.dumps(tfidf_transformer)
        self.cv = pickle.dumps(cv)
        self.save()

    def fit_keywords(self, qs):
        all_articles = qs.iterator()
        cv = pickle.loads(self.cv)
        tfidf_transformer = pickle.loads(self.tfidf_transformer)

        def sort_coo(coo_matrix):
            tuples = zip(coo_matrix.col, coo_matrix.data)
            return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

        def extract_topn_from_vector(feature_names, sorted_items, topn=10):
            """get the feature names and tf-idf score of top n items"""

            # use only topn items from vector
            sorted_items = sorted_items[:topn]

            score_vals = []
            feature_vals = []

            for idx, score in sorted_items:
                # keep track of feature name and its corresponding score
                score_vals.append(round(score, 3))
                feature_vals.append(feature_names[idx])

            # create a tuples of feature,score
            # results = zip(feature_vals,score_vals)
            results = {}
            for idx in range(len(feature_vals)):
                results[feature_vals[idx]] = score_vals[idx]

            return results

        # get feature names
        feature_names = cv.get_feature_names()

        def get_keywords(text, count):
            # generate tf-idf for the given document
            tf_idf_vector = tfidf_transformer.transform(
                cv.transform([text]))

            # sort the tf-idf vectors by descending order of scores
            sorted_items = sort_coo(tf_idf_vector.tocoo())

            # extract only the top n
            res = extract_topn_from_vector(
                feature_names, sorted_items, count)

            return map(str, res)

        def get_article_keywords(article):
            return set([
                *get_keywords(article.text_content, 75),
                *get_keywords(article.title, 5)
            ])

        all_keywords = set(self.keywords)

        # Process docs in chunks of 500
        for articles in grouper(500, all_articles):
            for article in articles:
                if article is not None:
                    keywords = get_article_keywords(article)
                    all_keywords.update(keywords)
                    article.tags.add(*keywords)

        self.keywords = sorted(all_keywords)
        self.save()


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)
