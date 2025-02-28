# Before you run migration script
# create instance of WebsiteAwardsIndexPage
# and then at least one WebsiteAwardPage instance


import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from website_awards.models import WebsiteAwardsIndexPage, WebsiteAwardPage

SOURCE_FILE = "awards.xml"

NAMESPACES = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}


def get_metadata_value(item, key):
    for postmeta in item.findall("wp:postmeta", NAMESPACES):
        meta_key = postmeta.find("wp:meta_key", NAMESPACES)
        meta_value = postmeta.find("wp:meta_value", NAMESPACES)

        if meta_key is not None and meta_value is not None and meta_key.text == key:
            return meta_value.text
    return None


def migrate_data(file):

    tree = ET.parse(file)
    root = tree.getroot()
    channel = root[0]
    items = channel.findall("item")

    awards = []
    for item in items:
        if (
            item.find("wp:post_type", NAMESPACES).text == "award"
            and item.find("wp:status", NAMESPACES).text == "publish"
        ):
            organisation = get_metadata_value(item, "organisation")
            year_awarded = get_metadata_value(item, "year_awarded")
            amount_awarded = get_metadata_value(item, "amount_awarded")
            website = get_metadata_value(item, "website")
            award_type = get_metadata_value(item, "award_type")

            if award_type == 'a:1:{i:0;s:8:"standard";}':
                award_type = "standard"
            elif award_type == 'a:1:{i:0;s:5:"major";}':
                award_type = "major"
            elif award_type == 'a:1:{i:0;s:11:"ninafishman";}':
                award_type = "ninafishman"

            awards.append(
                {
                    "title": item.find("title").text,
                    "post_date": item.find("wp:post_date", NAMESPACES).text[:10],
                    "organisation": organisation,
                    "year": year_awarded,
                    "amount_awarded": amount_awarded,
                    "website": website,
                    "award_type": award_type,
                    "content": item.find("content:encoded", NAMESPACES).text,
                }
            )

    for a in awards:
        award = WebsiteAwardPage(
            title=a["title"],
            content=a["content"],
            post_date=a["post_date"],
            organisation=a["organisation"],
            year=a["year"],
            amount_awarded=a["amount_awarded"],
            website=a["website"],
            award_type=a["award_type"],
        )

        awards_index_page = WebsiteAwardsIndexPage.objects.filter(
            title="Awards"
        ).first()

        try:
            awards_index_page.add_child(instance=award)
            awards_index_page.save()

        except ValidationError:
            print(f"Error while adding post titled {award.title}")
