from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("admin/_dashboard_stats.html")
def dashboard_stats():
    from website.models import (
        Attraction,
        BlogPost,
        Destination,
        Lead,
        Testimonial,
        ThingToDo,
        Tour,
    )

    return {
        "counts": {
            "destinations": Destination.objects.count(),
            "tours": Tour.objects.count(),
            "blog_posts": BlogPost.objects.count(),
            "leads": Lead.objects.count(),
            "testimonials": Testimonial.objects.count(),
            "attractions": Attraction.objects.count(),
            "things_to_do": ThingToDo.objects.count(),
        },
        "links": {
            "destinations": reverse("admin:website_destination_changelist"),
            "tours": reverse("admin:website_tour_changelist"),
            "blog_posts": reverse("admin:website_blogpost_changelist"),
            "leads": reverse("admin:website_lead_changelist"),
            "testimonials": reverse("admin:website_testimonial_changelist"),
            "attractions": reverse("admin:website_attraction_changelist"),
            "things_to_do": reverse("admin:website_thingtodo_changelist"),
        },
    }
