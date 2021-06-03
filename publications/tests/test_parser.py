from dateparser import parse
from unittest import TestCase

from publications import scraper


class ParseTest(TestCase):
    def test_7days(self):
        scraper.crawl_7days()

    def test_blackdwarf(self):
        scraper.crawl_blackdwarf()

    def test_newreasoner(self):
        scraper.crawl_newreasoner()
