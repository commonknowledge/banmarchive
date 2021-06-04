from dateparser import parse
from unittest import TestCase

from publications import scraper


class ParseTest(TestCase):
    def test_7days(self):
        self.assertNumberOfIssues(scraper.crawl_7days(), 21)

    def test_blackdwarf(self):
        self.assertNumberOfIssues(scraper.crawl_blackdwarf(), 40)

    def test_newreasoner(self):
        self.assertNumberOfIssues(scraper.crawl_newreasoner(), 10)

    def assertNumberOfIssues(self, publication, count):
        self.assertEqual(len(publication['issues']), count,
                         f'Expectyed publication to have {count} issues. Found {len(publication["issues"])}')
