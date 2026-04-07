"""Filter and sort tour querysets from GET parameters (list + category pages)."""

from decimal import Decimal, InvalidOperation

from django.db.models import F, Q, QuerySet


def _decimal(val: str | None) -> Decimal | None:
    if val is None or not str(val).strip():
        return None
    try:
        return Decimal(str(val).strip().replace(",", "."))
    except InvalidOperation:
        return None


def apply_tour_list_filters(qs: QuerySet, get_params) -> QuerySet:
    """
    Apply text search, price/rating/duration/language filters, feature toggles, and sort.
    `get_params` is request.GET (supports .get).
    """
    g = get_params

    q = (g.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(slug__icontains=q)
            | Q(teaser__icontains=q)
            | Q(body__icontains=q)
            | Q(languages__icontains=q)
        )

    min_p = _decimal(g.get("min_price"))
    if min_p is not None:
        qs = qs.filter(price_from__gte=min_p)

    max_p = _decimal(g.get("max_price"))
    if max_p is not None:
        qs = qs.filter(price_from__lte=max_p)

    min_r = _decimal(g.get("min_rating"))
    if min_r is not None:
        qs = qs.filter(rating_average__gte=min_r)

    max_d = _decimal(g.get("max_duration"))
    if max_d is not None:
        qs = qs.filter(duration_hours__lte=max_d)

    lang = (g.get("lang") or "").strip()
    if lang:
        qs = qs.filter(languages__icontains=lang)

    if g.get("free_cancel") == "1":
        qs = qs.filter(free_cancellation=True)
    if g.get("skip_line") == "1":
        qs = qs.filter(skip_the_line=True)
    if g.get("accessible") == "1":
        qs = qs.filter(wheelchair_accessible=True)

    sort = (g.get("sort") or "name").strip()
    if sort == "price_asc":
        qs = qs.order_by(F("price_from").asc(nulls_last=True), "name")
    elif sort == "price_desc":
        qs = qs.order_by(F("price_from").desc(nulls_last=True), "name")
    elif sort == "rating_desc":
        qs = qs.order_by(F("rating_average").desc(nulls_last=True), "name")
    elif sort == "duration_asc":
        qs = qs.order_by("duration_hours", "name")
    elif sort == "duration_desc":
        qs = qs.order_by(F("duration_hours").desc(nulls_last=True), "name")
    elif sort == "reviews_desc":
        qs = qs.order_by(F("review_count").desc(nulls_last=True), "name")
    else:
        qs = qs.order_by("name")

    return qs


def tour_filters_active(get_params) -> bool:
    g = get_params
    if (g.get("q") or "").strip():
        return True
    for k in ("min_price", "max_price", "min_rating", "max_duration", "lang"):
        if (g.get(k) or "").strip():
            return True
    if g.get("sort") and g.get("sort").strip() not in ("", "name"):
        return True
    if g.get("free_cancel") == "1" or g.get("skip_line") == "1" or g.get("accessible") == "1":
        return True
    return False


def tour_filter_form_context(get_params, *, filter_action_url: str) -> dict:
    """Defaults for filter form fields (templates)."""
    g = get_params
    return {
        "tour_filter_action": filter_action_url,
        "tour_filters_active": tour_filters_active(g),
        "tour_filter_q": (g.get("q") or "").strip(),
        "tour_filter_min_price": (g.get("min_price") or "").strip(),
        "tour_filter_max_price": (g.get("max_price") or "").strip(),
        "tour_filter_min_rating": (g.get("min_rating") or "").strip(),
        "tour_filter_max_duration": (g.get("max_duration") or "").strip(),
        "tour_filter_lang": (g.get("lang") or "").strip(),
        "tour_filter_sort": (g.get("sort") or "name").strip(),
        "tour_filter_free_cancel": g.get("free_cancel") == "1",
        "tour_filter_skip_line": g.get("skip_line") == "1",
        "tour_filter_accessible": g.get("accessible") == "1",
    }
