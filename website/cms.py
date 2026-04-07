from django.db import transaction

from .models import SitePage


def ensure_site_pages_exist():
    """Create default CMS rows for each fixed page key (idempotent)."""
    seeds = [
        (SitePage.PageKey.HOME, "Home"),
        (SitePage.PageKey.ABOUT, "About"),
        (SitePage.PageKey.CONTACT, "Contact"),
        (SitePage.PageKey.FAQS, "FAQs"),
        (SitePage.PageKey.LEGAL, "Legal"),
    ]
    with transaction.atomic():
        for key, title in seeds:
            SitePage.objects.get_or_create(
                page_key=key,
                defaults={"title": title},
            )


def get_site_page(page_key: str) -> SitePage:
    qs = SitePage.objects.prefetch_related(
        "featured_destinations",
        "featured_blog_posts",
        "featured_tours__destination",
        "featured_attractions__destination",
        "featured_things_to_do__destination",
    )
    try:
        return qs.get(page_key=page_key)
    except SitePage.DoesNotExist:
        ensure_site_pages_exist()
        return qs.get(page_key=page_key)
