from wagtail.core.models import Site
from helpers.cache import django_cached
from django.views.generic import TemplateView
from django.template.defaultfilters import slugify

from publications import models


class ImportView(TemplateView):
    template_name = 'publications/admin_upload.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            examples=[
                row
                for issue in self.get_example_issues()
                for row in self.get_example_issue_import_rows(issue)
            ],
            archive_root=self.get_root_page_id()
        )

    def get_root_page_id(self):
        site = Site.find_for_request(self.request)
        if site is not None:
            return site.root_page.id

        return 1

    # @django_cached('publications.views.ImportView.get_example_issue_import_rows')
    def get_example_issue_import_rows(self, issue):
        articles = [
            {
                'filename': slugify(issue.title + '_' + article.title) + '.pdf',
                'article_title': get(article, 'title'),
                'author': get(article, 'author_name'),
                "publication": get(issue, 'publication', 'title'),
                'issue_title': get(issue, 'title'),
                'publication_date': get(issue, 'publication_date'),
                "volume_no": get(issue, 'volume'),
                "issue_no": get(issue, 'issue'),
                'is_cover': None

            }
            for article in issue.articles
        ]

        if issue.issue_cover is not None:
            articles.append(
                {
                    'filename': slugify(issue.title + '_' + 'cover') + '.pdf',
                    'article_title': None,
                    'author': None,
                    "publication": get(issue, 'publication', 'title'),
                    'issue_title': get(issue, 'title'),
                    'publication_date': get(issue, 'publication_date'),
                    "volume_no": get(issue, 'volume'),
                    "issue_no": get(issue, 'issue'),
                    'is_cover': '1'
                }
            )

        return articles

    def get_example_issues(self):
        issues = []

        for iss in models.MultiArticleIssue.objects.iterator():
            if iss.issue_cover is None:
                continue

            if next((x for x in iss.articles if x.author_name), None) == None:
                continue

            if iss.articles.count() < 3:
                continue

            issues.append(iss)

            if len(issues) >= 3:
                break

        return issues


def get(x, *path):
    for p in path:
        if x is None:
            return None

        x = getattr(x, p)

    return x
