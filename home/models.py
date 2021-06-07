from wagtail.core.models import Page

from helpers.content import get_children_of_type
from publications.models import Publication


class HomePage(Page):
    @property
    def publications(self):
        return get_children_of_type(self, Publication)
