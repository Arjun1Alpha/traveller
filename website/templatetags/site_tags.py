from django import template

register = template.Library()


@register.simple_tag
def cw_href(link):
    """Normalize admin-entered links: paths or full URLs."""
    if not link:
        return "#"
    link = str(link).strip()
    if link.startswith(("http://", "https://", "//")):
        return link
    if link.startswith("/"):
        return link
    return f"/{link}"
