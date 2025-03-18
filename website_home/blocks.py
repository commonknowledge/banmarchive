from wagtail.core import blocks


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
