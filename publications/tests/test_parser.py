from dateparser import parse
from django.test import TestCase

from publications import scraper


class ParseTest(TestCase):
    # def test_7days(self):
    #     scraper.crawl_7days()

    def test_blackdwarf(self):
        scraper.crawl_blackdwarf()
