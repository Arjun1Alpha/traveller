# Generated manually — remove demo example.com header links so /account and /cart work on-site.

from django.db import migrations


def clear_example_header_urls(apps, schema_editor):
    SiteSettings = apps.get_model("website", "SiteSettings")
    for s in SiteSettings.objects.all():
        changed = False
        u = (s.header_account_url or "").lower()
        if "example.com" in u or u.strip() in ("https://example.com/account", "http://example.com/account"):
            s.header_account_url = ""
            changed = True
        c = (s.header_cart_url or "").lower()
        if "example.com" in c or c.strip() in ("https://example.com/cart", "http://example.com/cart"):
            s.header_cart_url = ""
            changed = True
        if changed:
            s.save(update_fields=["header_account_url", "header_cart_url"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0007_accounts_cart_profile_lead"),
    ]

    operations = [
        migrations.RunPython(clear_example_header_urls, noop),
    ]
