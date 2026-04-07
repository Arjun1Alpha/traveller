from .cart import cart_item_count_for_request
from .models import (
    Destination,
    FooterNavLink,
    FooterTrustBadge,
    PressMention,
    SiteSettings,
    SocialLink,
)


def account_chrome(request):
    return {"cart_item_count": cart_item_count_for_request(request)}


def site_chrome(request):
    site_settings = SiteSettings.load()
    return {
        "site_settings": site_settings,
        "nav_destinations": Destination.objects.order_by("name")[:14],
        "footer_company_links": FooterNavLink.objects.filter(
            column=FooterNavLink.Column.COMPANY
        ).order_by("sort_order"),
        "footer_help_links": FooterNavLink.objects.filter(
            column=FooterNavLink.Column.HELP
        ).order_by("sort_order"),
        "footer_trust_badges": FooterTrustBadge.objects.order_by("sort_order"),
        "social_links": SocialLink.objects.order_by("sort_order"),
        "press_mentions": PressMention.objects.order_by("sort_order"),
    }
