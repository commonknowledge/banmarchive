from django.core.management.base import BaseCommand
from requests.auth import HTTPBasicAuth

from publications import models, serializers, scraper


class Command(BaseCommand):
    help = 'Dump a local archive to stdout'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
        )

    def handle(self, *args, root, **kwargs):
        from sys import stdout
        from publications.models import Article, MultiArticleIssue, Publication
        import csv

        pub = Publication.objects.get(pk=int(root))
        writer = csv.DictWriter(stdout, ('filename', 'article_title', 'author', 'publication',
                                         'issue_title', 'publication_date', 'volume_no', 'issue_no',
                                         'is_cover'))

        writer.writeheader()
        for issue in MultiArticleIssue.objects.child_of(pub):
            if issue.pdf:
                writer.writerow({
                    'filename': issue.pdf.file.name,
                    'article_title': 'Covers',
                    'author': '',
                    'publication': pub.title,
                    'issue_title': issue.title,
                    'publication_date': issue.publication_date,
                    'volume_no': issue.volume,
                    'issue_no': issue.issue,
                    'is_cover': 1
                })

            for article in Article.objects.child_of(issue):
                writer.writerow({
                    'filename': article.pdf.file.name,
                    'article_title': article.title,
                    'author': article.author_name,
                    'publication': pub.title,
                    'issue_title': issue.title,
                    'publication_date': issue.publication_date,
                    'volume_no': issue.volume,
                    'issue_no': issue.issue,
                    'is_cover': ''
                })
