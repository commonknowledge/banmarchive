from wagtail.core.models import Page

from helpers.content import get_children_of_type, random_model
from publications.models import Publication


class HomePage(Page):
    @property
    def publications(self):
        return get_children_of_type(self, Publication)

    @property
    def issue_sample(self):
        return (
            p.random_issue
            for p in random_model(self.publications, count=4)
        )
