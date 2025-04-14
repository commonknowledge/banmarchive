from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


class HomePageTeaserBlock(blocks.StructBlock):
    label = blocks.CharBlock()
    title = blocks.CharBlock()
    description = blocks.CharBlock()
    page = blocks.PageChooserBlock(required=False)
    external_link = blocks.URLBlock(required=False)
    call_to_action = blocks.CharBlock()
    highlighted = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "pick"
        template = "blocks/home_page_teaser_block.html"


class TrusteeBlock(blocks.StructBlock):
    name = blocks.CharBlock(required=True)
    role = blocks.CharBlock(required=False)
    image = ImageChooserBlock(required=False)
    bio = blocks.RichTextBlock(
        features=["bold", "italic", "ul", "ol", "link"],
        required=False,
    )

    class Meta:
        template = "blocks/trustee-block.html"
        label = "Trustee member"
        icon = "user"
