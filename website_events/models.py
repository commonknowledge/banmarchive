from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core.fields import RichTextField


class WebsiteEventIndexPage(Page):
    max_count = 1

    parent_page_types = ["website_home.WebsiteHomePage"]
    subpage_types = ["website_events.WebsiteEventPage"]

    def get_context(self, request):
        context = super().get_context(request)

        today = now().date()
        current_time = now().time()

        upcoming_events = (
            WebsiteEventPage.objects.live()
            .filter(
                models.Q(date__gt=today)  # Future events
                | models.Q(date=today, all_day=True)  # Today’s all-day events
                | models.Q(
                    date=today, all_day=False, end_time__gte=current_time
                )  # Today’s events that haven’t ended
            )
            .order_by("date", "start_time")
        )

        # Past events
        past_events = (
            WebsiteEventPage.objects.live()
            .filter(
                models.Q(date__lt=today)  # Past events
                | models.Q(
                    date=today, all_day=False, end_time__lt=current_time
                )  # Today's events that have ended
            )
            .order_by("-date", "-start_time")
        )

        context["upcoming_events"] = upcoming_events
        context["past_events"] = past_events

        return context


class WebsiteEventPage(Page):
    location = models.CharField(max_length=500, null=True, blank=True)
    copy = RichTextField()
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)

    parent_page_types = ["website_events.WebsiteEventIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("copy"),
        FieldPanel("location"),
        FieldPanel("date"),
        FieldPanel("all_day"),
        MultiFieldPanel(
            (
                FieldPanel("start_time"),
                FieldPanel("end_time"),
            ),
            "Start and end time",
        ),
    ]

    def clean(self):
        """Custom validation logic"""
        if self.all_day:
            self.start_time = None
            self.end_time = None
        else:
            if not self.start_time:
                raise ValidationError(
                    {
                        "start_time": "Start time is required if the event is not all-day."
                    }
                )
            if not self.end_time:
                raise ValidationError(
                    {"end_time": "End time is required if the event is not all-day."}
                )

        super().clean()

    def save(self, *args, **kwargs):
        """Ensure validation runs before saving"""
        self.clean()
        super().save(*args, **kwargs)
