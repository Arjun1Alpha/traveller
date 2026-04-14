from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .cms import get_site_page
from .forms import LeadForm
from .tour_query import apply_tour_list_filters, tour_filter_form_context
from .models import (
    Attraction,
    AttractionGalleryImage,
    BlogPost,
    CategoryGalleryImage,
    Destination,
    DestinationCategory,
    GalleryImage,
    HomeIconFeature,
    HomePageConfig,
    Lead,
    SitePage,
    SiteSettings,
    Testimonial,
    ThingToDo,
    ThingToDoGalleryImage,
    Tour,
    TourGalleryImage,
)


def safe_next(request):
    n = request.POST.get("next") or "/"
    if url_has_allowed_host_and_scheme(
        n,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return n
    return "/"


def _cms_context(page_key: str, *, show_lead: bool):
    page = get_site_page(page_key)
    ctx = {"site_page": page}
    if show_lead or page.show_lead_form:
        ctx["lead_form"] = LeadForm(
            initial={
                "source_page": page_key,
                "next": reverse(_url_name_for_page_key(page_key)),
            }
        )
    return ctx


def _url_name_for_page_key(page_key: str) -> str:
    return {
        SitePage.PageKey.HOME: "home",
        SitePage.PageKey.ABOUT: "about",
        SitePage.PageKey.CONTACT: "contact",
        SitePage.PageKey.FAQS: "faqs",
        SitePage.PageKey.LEGAL: "legal",
    }[page_key]


_FALLBACK_CARD_IMAGES = [
    "https://images.unsplash.com/photo-1552832230-c0197dd771b6?w=800&q=80",
    "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&q=80",
    "https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=800&q=80",
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80",
    "https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=800&q=80",
    "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=800&q=80",
    "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800&q=80",
    "https://images.unsplash.com/photo-1529154036614-a60975f5c760?w=800&q=80",
]

_DEFAULT_HERO = (
    "https://images.unsplash.com/photo-1529154036614-a60975f5c760?w=2400&q=85"
)

# Shown when there are no active Testimonial rows (empty list is falsy in templates).
_FALLBACK_HOME_TESTIMONIALS = [
    SimpleNamespace(
        quote="Flawless from booking to the final stop. Our guide made Rome unforgettable.",
        author="Sarah M., Chicago",
        rating=5,
    ),
    SimpleNamespace(
        quote="Skip-the-line was worth every penny. Small group, big memories.",
        author="James L., London",
        rating=5,
    ),
    SimpleNamespace(
        quote="Professional, friendly, and deeply knowledgeable. Already planning our next trip.",
        author="Elena R., Madrid",
        rating=5,
    ),
]


def _testimonials_for_home():
    rows = list(Testimonial.objects.filter(is_active=True).order_by("sort_order"))
    return rows if rows else _FALLBACK_HOME_TESTIMONIALS


def _testimonials_for_page(**entity):
    """Prefer testimonials tagged for this category/tour/attraction/thing; else global active."""
    q = Q()
    if entity.get("category") is not None:
        c = entity["category"]
        q |= Q(related_categories=c)
        q |= Q(related_tours__category=c)
    if entity.get("tour") is not None:
        t = entity["tour"]
        q |= Q(related_tours=t)
        if t.category_id:
            q |= Q(related_categories=t.category)
    if entity.get("attraction") is not None:
        q |= Q(related_attractions=entity["attraction"])
    if entity.get("thing") is not None:
        q |= Q(related_things_to_do=entity["thing"])
    base = Testimonial.objects.filter(is_active=True)
    if q:
        tagged = list(base.filter(q).distinct().order_by("sort_order", "id"))
        if tagged:
            return tagged
    fallback = list(base.order_by("sort_order", "id")[:12])
    return fallback if fallback else _FALLBACK_HOME_TESTIMONIALS


def _blog_posts_for_entity(*, category=None, attraction=None, thing=None):
    """
    Posts explicitly tagged to the entity, plus city-level posts (related_destinations)
    and (for categories) posts tagged to any tour in that category.
    """
    q = Q()
    destination = None
    if category is not None:
        destination = category.destination
        q |= Q(related_categories=category)
        q |= Q(related_tours__category=category)
    elif attraction is not None:
        destination = attraction.destination
        q |= Q(related_attractions=attraction)
    elif thing is not None:
        destination = thing.destination
        q |= Q(related_things_to_do=thing)
    else:
        return []
    if destination is not None:
        q |= Q(related_destinations=destination)
    return list(
        BlogPost.objects.filter(q)
        .distinct()
        .order_by("-published_at", "title")[:12]
    )


def _blog_posts_for_destination_listing(destination, *, scope):
    """scope: categories | tours | attractions | things"""
    if scope == "categories":
        q = Q(related_categories__destination=destination)
    elif scope == "tours":
        q = Q(related_tours__destination=destination) | Q(
            related_destinations=destination
        )
    elif scope == "attractions":
        q = Q(related_attractions__destination=destination)
    elif scope == "things":
        q = Q(related_things_to_do__destination=destination)
    else:
        return []
    return list(
        BlogPost.objects.filter(q)
        .distinct()
        .order_by("-published_at", "title")[:12]
    )


def _testimonials_for_destination_listing(destination, *, scope):
    if scope == "categories":
        q = Q(related_categories__destination=destination)
    elif scope == "tours":
        q = Q(related_tours__destination=destination)
    elif scope == "attractions":
        q = Q(related_attractions__destination=destination)
    elif scope == "things":
        q = Q(related_things_to_do__destination=destination)
    else:
        q = Q()
    base = Testimonial.objects.filter(is_active=True)
    if q:
        tagged = list(base.filter(q).distinct().order_by("sort_order", "id"))
        if tagged:
            return tagged
    fallback = list(base.order_by("sort_order", "id")[:12])
    return fallback if fallback else _FALLBACK_HOME_TESTIMONIALS


def _gallery_images_for_destination_listing(destination, *, scope):
    if scope == "categories":
        qs = CategoryGalleryImage.objects.filter(
            category__destination=destination, is_active=True
        )
    elif scope == "tours":
        qs = TourGalleryImage.objects.filter(
            tour__destination=destination, is_active=True
        )
    elif scope == "attractions":
        qs = AttractionGalleryImage.objects.filter(
            attraction__destination=destination, is_active=True
        )
    elif scope == "things":
        qs = ThingToDoGalleryImage.objects.filter(
            thing_to_do__destination=destination, is_active=True
        )
    else:
        return []
    return list(qs.order_by("sort_order", "id")[:24])


_SEARCH_RESULTS_LIMIT = 30
_BLOG_PER_PAGE = 9


def home(request):
    site_settings = SiteSettings.load()
    home_cfg = HomePageConfig.load()
    ctx = _cms_context(SitePage.PageKey.HOME, show_lead=False)
    ctx["home_cfg"] = home_cfg
    ctx["hero_image_url"] = (
        home_cfg.hero_image_url
        or site_settings.default_hero_image_url
        or _DEFAULT_HERO
    )

    lim = home_cfg.home_destinations_limit or 8
    pinned = Destination.objects.filter(show_on_homepage=True).order_by(
        "homepage_order", "name"
    )
    if pinned.exists():
        dests = list(pinned[:lim])
    else:
        dests = list(Destination.objects.order_by("name")[:lim])

    nfb = len(_FALLBACK_CARD_IMAGES)
    default_card = site_settings.default_card_image_url
    tour_stats_qs = (
        Tour.objects.filter(destination__in=dests)
        .values("destination_id")
        .annotate(
            min_price=Min("price_from"),
            min_duration=Min("duration_hours"),
        )
    )
    tour_stats = {row["destination_id"]: row for row in tour_stats_qs}
    ctx["destination_showcase"] = [
        (
            d,
            (d.listing_image_url or default_card or _FALLBACK_CARD_IMAGES[i % nfb]),
            tour_stats.get(d.id, {}),
        )
        for i, d in enumerate(dests)
    ]

    blog_n = home_cfg.blog_cards_limit or 4
    ctx["home_blog_posts"] = list(
        BlogPost.objects.order_by("-published_at", "title")[:blog_n]
    )

    ctx["hero_icon_features"] = list(
        HomeIconFeature.objects.filter(
            section=HomeIconFeature.Section.HERO_OVERLAY,
            is_active=True,
        ).order_by("sort_order")
    )
    ctx["sky_icon_features"] = list(
        HomeIconFeature.objects.filter(
            section=HomeIconFeature.Section.SKY_STRIP,
            is_active=True,
        ).order_by("sort_order")
    )
    ctx["promise_icon_features"] = list(
        HomeIconFeature.objects.filter(
            section=HomeIconFeature.Section.PROMISE,
            is_active=True,
        ).order_by("sort_order")
    )
    ctx["testimonials"] = _testimonials_for_home()
    ctx["gallery_images"] = list(
        GalleryImage.objects.filter(is_active=True).order_by("sort_order")[:12]
    )
    ctx["expert_bullets"] = list(
        home_cfg.expert_bullets.order_by("sort_order")
    )
    ctx["query_destinations"] = list(Destination.objects.order_by("name")[:50])
    ctx["query_categories"] = list(
        DestinationCategory.objects.select_related("destination")
        .order_by("destination__name", "name")[:80]
    )
    ctx["query_tours"] = list(
        Tour.objects.select_related("destination")
        .order_by("destination__name", "name")[:80]
    )
    return render(request, "website/home.html", ctx)


def search(request):
    q = request.GET.get("q", "").strip()
    people_raw = request.GET.get("people", "").strip()
    people_count = None
    for token in people_raw.replace("+", " ").split():
        if token.isdigit():
            people_count = int(token)
            break

    ctx = {
        "search_q": q,
        "search_limit": _SEARCH_RESULTS_LIMIT,
        "search_people": people_raw,
    }
    if not q and people_count is None:
        return render(request, "website/search.html", ctx)

    dest_q = (
        Q(name__icontains=q)
        | Q(slug__icontains=q)
        | Q(summary__icontains=q)
    )
    blog_q = (
        Q(title__icontains=q)
        | Q(slug__icontains=q)
        | Q(excerpt__icontains=q)
        | Q(body__icontains=q)
    )
    tour_q = (
        Q(name__icontains=q)
        | Q(slug__icontains=q)
        | Q(teaser__icontains=q)
        | Q(body__icontains=q)
        | Q(languages__icontains=q)
    )
    att_q = Q(name__icontains=q) | Q(slug__icontains=q) | Q(summary__icontains=q)
    todo_q = Q(name__icontains=q) | Q(slug__icontains=q) | Q(summary__icontains=q)

    if q:
        ctx["result_destinations"] = list(
            Destination.objects.filter(dest_q).order_by("name")[:_SEARCH_RESULTS_LIMIT]
        )
        ctx["result_blog_posts"] = list(
            BlogPost.objects.filter(blog_q)
            .order_by("-published_at", "title")[:_SEARCH_RESULTS_LIMIT]
        )
        ctx["result_attractions"] = list(
            Attraction.objects.filter(att_q)
            .select_related("destination")
            .order_by("destination__name", "name")[:_SEARCH_RESULTS_LIMIT]
        )
        ctx["result_things"] = list(
            ThingToDo.objects.filter(todo_q)
            .select_related("destination")
            .order_by("destination__name", "name")[:_SEARCH_RESULTS_LIMIT]
        )
    else:
        ctx["result_destinations"] = []
        ctx["result_blog_posts"] = []
        ctx["result_attractions"] = []
        ctx["result_things"] = []

    tours_qs = Tour.objects.select_related("destination", "category")
    if q:
        tours_qs = tours_qs.filter(tour_q)
    if people_count is not None:
        tours_qs = tours_qs.filter(
            Q(group_size_max__gte=people_count) | Q(group_size_max__isnull=True)
        )
    ctx["result_tours"] = list(
        tours_qs.order_by("destination__name", "name")[:_SEARCH_RESULTS_LIMIT]
    )
    ctx["total_matches"] = (
        len(ctx["result_destinations"])
        + len(ctx["result_blog_posts"])
        + len(ctx["result_tours"])
        + len(ctx["result_attractions"])
        + len(ctx["result_things"])
    )
    return render(request, "website/search.html", ctx)


def destination_list(request):
    destinations = Destination.objects.annotate(
        tour_count=Count("tours", distinct=True),
        category_count=Count("categories", distinct=True),
        attraction_count=Count("attractions", distinct=True),
        thing_count=Count("things_to_do", distinct=True),
    ).order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        destinations = destinations.filter(
            Q(name__icontains=q) | Q(slug__icontains=q) | Q(summary__icontains=q)
        )
    return render(
        request,
        "website/destinations/list.html",
        {"destinations": destinations, "search_q": q},
    )


def destination_hub(request, dest_slug):
    destination = get_object_or_404(
        Destination.objects.annotate(
            tour_count=Count("tours", distinct=True),
            category_count=Count("categories", distinct=True),
            attraction_count=Count("attractions", distinct=True),
            thing_count=Count("things_to_do", distinct=True),
        ),
        slug=dest_slug,
    )
    related_blog_posts = list(
        BlogPost.objects.filter(related_destinations=destination)
        .order_by("-published_at", "title")
        .prefetch_related("related_tours__destination")
        .distinct()[:12]
    )
    site_settings = SiteSettings.load()
    _fb_i = sum(ord(c) for c in destination.slug) % len(_FALLBACK_CARD_IMAGES)
    hub_hero_image_url = (
        destination.listing_image_url
        or site_settings.default_card_image_url
        or _FALLBACK_CARD_IMAGES[_fb_i]
    )
    dest_categories = list(destination.categories.order_by("name")[:12])
    dest_tours = list(
        destination.tours.select_related("category").order_by("name")[:8]
    )
    dest_attractions = list(destination.attractions.order_by("name")[:8])
    dest_things = list(destination.things_to_do.order_by("name")[:8])
    testimonial_rows = list(
        Testimonial.objects.filter(is_active=True).order_by("sort_order")[:12]
    )
    destination_testimonials = (
        testimonial_rows if testimonial_rows else _FALLBACK_HOME_TESTIMONIALS
    )
    return render(
        request,
        "website/destinations/hub.html",
        {
            "destination": destination,
            "related_blog_posts": related_blog_posts,
            "hub_hero_image_url": hub_hero_image_url,
            "dest_categories": dest_categories,
            "dest_tours": dest_tours,
            "dest_attractions": dest_attractions,
            "dest_things": dest_things,
            "destination_testimonials": destination_testimonials,
        },
    )


def destination_categories(request, dest_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    categories = (
        destination.categories.annotate(tour_count=Count("tours", distinct=True))
        .order_by("name")
    )
    return render(
        request,
        "website/destinations/categories.html",
        {
            "destination": destination,
            "categories": categories,
            "listing_gallery_images": _gallery_images_for_destination_listing(
                destination, scope="categories"
            ),
            "listing_blog_posts": _blog_posts_for_destination_listing(
                destination, scope="categories"
            ),
            "listing_testimonials": _testimonials_for_destination_listing(
                destination, scope="categories"
            ),
        },
    )


def destination_category_detail(request, dest_slug, cat_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    category = get_object_or_404(
        DestinationCategory, destination=destination, slug=cat_slug
    )
    tours = Tour.objects.filter(
        destination=destination, category=category
    ).select_related("category")
    tours = apply_tour_list_filters(tours, request.GET)
    filter_ctx = tour_filter_form_context(
        request.GET, filter_action_url=category.get_absolute_url()
    )
    category_gallery_images = list(
        category.gallery_images.filter(is_active=True).order_by("sort_order", "id")
    )
    category_blog_posts = _blog_posts_for_entity(category=category)
    page_testimonials = _testimonials_for_page(category=category)
    return render(
        request,
        "website/destinations/category_detail.html",
        {
            "destination": destination,
            "category": category,
            "tours": tours,
            "tour_search_q": filter_ctx["tour_filter_q"],
            **filter_ctx,
            "category_gallery_images": category_gallery_images,
            "category_blog_posts": category_blog_posts,
            "page_testimonials": page_testimonials,
        },
    )


def tour_list(request, dest_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    tours = destination.tours.select_related("category")
    tours = apply_tour_list_filters(tours, request.GET)
    filter_ctx = tour_filter_form_context(
        request.GET,
        filter_action_url=reverse("tour_list", kwargs={"dest_slug": dest_slug}),
    )
    return render(
        request,
        "website/destinations/tours/list.html",
        {
            "destination": destination,
            "tours": tours,
            "tour_search_q": filter_ctx["tour_filter_q"],
            **filter_ctx,
            "listing_gallery_images": _gallery_images_for_destination_listing(
                destination, scope="tours"
            ),
            "listing_blog_posts": _blog_posts_for_destination_listing(
                destination, scope="tours"
            ),
            "listing_testimonials": _testimonials_for_destination_listing(
                destination, scope="tours"
            ),
        },
    )


def tour_pdp(request, dest_slug, tour_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    tour = get_object_or_404(
        Tour.objects.select_related("category"),
        destination=destination,
        slug=tour_slug,
    )
    blog_q = Q(related_tours=tour) | Q(related_destinations=destination)
    if tour.category_id:
        blog_q |= Q(related_categories=tour.category)
    related_blog_posts = list(
        BlogPost.objects.filter(blog_q)
        .distinct()
        .order_by("-published_at", "title")[:12]
    )
    tour_gallery_images = list(
        tour.gallery_images.filter(is_active=True).order_by("sort_order", "id")
    )
    page_testimonials = _testimonials_for_page(tour=tour)
    return render(
        request,
        "website/destinations/tours/detail.html",
        {
            "destination": destination,
            "tour": tour,
            "related_blog_posts": related_blog_posts,
            "tour_gallery_images": tour_gallery_images,
            "page_testimonials": page_testimonials,
        },
    )


@login_required
@require_POST
def tour_inquiry_submit(request, dest_slug, tour_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    tour = get_object_or_404(
        Tour,
        destination=destination,
        slug=tour_slug,
    )
    message = (request.POST.get("message") or "").strip()
    if not message:
        messages.error(request, "Please enter a short message.")
        return HttpResponseRedirect(tour.get_absolute_url())
    u = request.user
    name = (u.get_full_name() or u.get_username())[:120]
    email = u.email
    phone = (u.profile.phone or "")[:40] if hasattr(u, "profile") else ""
    Lead.objects.create(
        name=name,
        email=email,
        phone=phone,
        message=message,
        destination_interest=destination,
        user=u,
        related_tour=tour,
        source_page="tour_pdp",
    )
    messages.success(request, "Thanks — we’ll get back to you about this tour.")
    return HttpResponseRedirect(tour.get_absolute_url())


def destination_attractions(request, dest_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    attractions = destination.attractions.order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        attractions = attractions.filter(
            Q(name__icontains=q)
            | Q(slug__icontains=q)
            | Q(summary__icontains=q)
        )
    return render(
        request,
        "website/destinations/attractions.html",
        {
            "destination": destination,
            "attractions": attractions,
            "attraction_search_q": q,
            "listing_gallery_images": _gallery_images_for_destination_listing(
                destination, scope="attractions"
            ),
            "listing_blog_posts": _blog_posts_for_destination_listing(
                destination, scope="attractions"
            ),
            "listing_testimonials": _testimonials_for_destination_listing(
                destination, scope="attractions"
            ),
        },
    )


def attraction_detail(request, dest_slug, attraction_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    attraction = get_object_or_404(
        Attraction, destination=destination, slug=attraction_slug
    )
    gallery_images = list(
        attraction.gallery_images.filter(is_active=True).order_by("sort_order", "id")
    )
    related_blog_posts = _blog_posts_for_entity(attraction=attraction)
    page_testimonials = _testimonials_for_page(attraction=attraction)
    return render(
        request,
        "website/destinations/attraction_detail.html",
        {
            "destination": destination,
            "attraction": attraction,
            "gallery_images": gallery_images,
            "related_blog_posts": related_blog_posts,
            "page_testimonials": page_testimonials,
        },
    )


def destination_things_to_do(request, dest_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    things = destination.things_to_do.order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        things = things.filter(
            Q(name__icontains=q)
            | Q(slug__icontains=q)
            | Q(summary__icontains=q)
        )
    return render(
        request,
        "website/destinations/things_to_do.html",
        {
            "destination": destination,
            "things": things,
            "things_search_q": q,
            "listing_gallery_images": _gallery_images_for_destination_listing(
                destination, scope="things"
            ),
            "listing_blog_posts": _blog_posts_for_destination_listing(
                destination, scope="things"
            ),
            "listing_testimonials": _testimonials_for_destination_listing(
                destination, scope="things"
            ),
        },
    )


def thing_to_do_detail(request, dest_slug, thing_slug):
    destination = get_object_or_404(Destination, slug=dest_slug)
    thing = get_object_or_404(
        ThingToDo, destination=destination, slug=thing_slug
    )
    gallery_images = list(
        thing.gallery_images.filter(is_active=True).order_by("sort_order", "id")
    )
    related_blog_posts = _blog_posts_for_entity(thing=thing)
    page_testimonials = _testimonials_for_page(thing=thing)
    return render(
        request,
        "website/destinations/thing_detail.html",
        {
            "destination": destination,
            "thing": thing,
            "gallery_images": gallery_images,
            "related_blog_posts": related_blog_posts,
            "page_testimonials": page_testimonials,
        },
    )


def blog_index(request):
    posts = BlogPost.objects.order_by("-published_at", "title")
    q = request.GET.get("q", "").strip()
    if q:
        posts = posts.filter(
            Q(title__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(body__icontains=q)
            | Q(slug__icontains=q)
        )
    paginator = Paginator(posts, _BLOG_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "website/blog/index.html",
        {
            "posts": page_obj,
            "page_obj": page_obj,
            "blog_search_q": q,
        },
    )


def blog_country(request, country_slug):
    posts_qs = BlogPost.objects.filter(
        scope=BlogPost.Scope.COUNTRY,
        country_slug=country_slug,
    ).order_by("-published_at", "title")
    paginator = Paginator(posts_qs, _BLOG_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    destination = Destination.objects.filter(slug=country_slug).first()
    city_story_slugs = list(
        BlogPost.objects.filter(
            scope=BlogPost.Scope.CITY,
            country_slug=country_slug,
        )
        .exclude(city_slug="")
        .values_list("city_slug", flat=True)
        .distinct()
        .order_by("city_slug")[:10]
    )
    related_destinations = list(
        Destination.objects.filter(
            blog_posts_tagged__scope=BlogPost.Scope.COUNTRY,
            blog_posts_tagged__country_slug=country_slug,
        )
        .distinct()
        .order_by("name")[:8]
    )
    related_destinations_sidebar = [
        d
        for d in related_destinations
        if not destination or d.pk != destination.pk
    ]
    related_tours = list(
        Tour.objects.filter(
            blog_posts_tagged__scope=BlogPost.Scope.COUNTRY,
            blog_posts_tagged__country_slug=country_slug,
        )
        .select_related("destination")
        .distinct()
        .order_by("destination__name", "name")[:8]
    )

    return render(
        request,
        "website/blog/country.html",
        {
            "country_slug": country_slug,
            "posts": page_obj,
            "page_obj": page_obj,
            "destination": destination,
            "city_story_slugs": city_story_slugs,
            "related_destinations_sidebar": related_destinations_sidebar,
            "related_tours": related_tours,
        },
    )


def blog_city(request, city_slug):
    posts_qs = BlogPost.objects.filter(
        scope=BlogPost.Scope.CITY,
        city_slug=city_slug,
    ).order_by("-published_at", "title")
    paginator = Paginator(posts_qs, _BLOG_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    destination = Destination.objects.filter(slug=city_slug).first()
    related_country_slug = (
        posts_qs.exclude(country_slug="")
        .order_by("-published_at")
        .values_list("country_slug", flat=True)
        .first()
    )
    related_destinations = list(
        Destination.objects.filter(
            blog_posts_tagged__scope=BlogPost.Scope.CITY,
            blog_posts_tagged__city_slug=city_slug,
        )
        .distinct()
        .order_by("name")[:8]
    )
    related_destinations_sidebar = [
        d
        for d in related_destinations
        if not destination or d.pk != destination.pk
    ]
    related_tours = list(
        Tour.objects.filter(
            blog_posts_tagged__scope=BlogPost.Scope.CITY,
            blog_posts_tagged__city_slug=city_slug,
        )
        .select_related("destination")
        .distinct()
        .order_by("destination__name", "name")[:8]
    )

    return render(
        request,
        "website/blog/city.html",
        {
            "city_slug": city_slug,
            "posts": page_obj,
            "page_obj": page_obj,
            "destination": destination,
            "related_country_slug": related_country_slug,
            "related_destinations_sidebar": related_destinations_sidebar,
            "related_tours": related_tours,
        },
    )


def blog_post_detail(request, post_slug):
    post = get_object_or_404(
        BlogPost.objects.prefetch_related(
            "related_destinations",
            "related_tours__destination",
            "related_categories__destination",
            "related_attractions__destination",
            "related_things_to_do__destination",
            "related_posts",
        ),
        slug=post_slug,
    )
    manual_related = list(post.related_posts.all()[:6])
    related_reading = manual_related[:6]
    seen = {post.pk} | {p.pk for p in related_reading}
    if len(related_reading) < 6:
        qs = BlogPost.objects.exclude(pk=post.pk).order_by("-published_at", "title")
        if post.scope == BlogPost.Scope.CITY and post.city_slug:
            qs = qs.filter(city_slug=post.city_slug)
        elif post.scope == BlogPost.Scope.COUNTRY and post.country_slug:
            qs = qs.filter(country_slug=post.country_slug)
        for p in qs[:24]:
            if p.pk in seen:
                continue
            related_reading.append(p)
            seen.add(p.pk)
            if len(related_reading) >= 6:
                break
    return render(
        request,
        "website/blog/post_detail.html",
        {
            "post": post,
            "related_reading": related_reading,
        },
    )


def about(request):
    ctx = _cms_context(SitePage.PageKey.ABOUT, show_lead=False)
    page = ctx["site_page"]
    site_settings = SiteSettings.load()
    dests = list(page.featured_destinations.all())
    nfb = len(_FALLBACK_CARD_IMAGES)
    default_card = site_settings.default_card_image_url
    ctx["about_dest_slider"] = [
        (
            d,
            d.listing_image_url or default_card or _FALLBACK_CARD_IMAGES[i % nfb],
        )
        for i, d in enumerate(dests)
    ]
    if dests:
        first_url = dests[0].listing_image_url or default_card
        ctx["about_hero_image"] = first_url or _FALLBACK_CARD_IMAGES[0]
    else:
        ctx["about_hero_image"] = (
            site_settings.default_hero_image_url
            or default_card
            or _DEFAULT_HERO
        )
    ctx["about_gallery"] = list(
        GalleryImage.objects.filter(is_active=True).order_by("sort_order")[:14]
    )
    ctx["about_testimonials"] = _testimonials_for_home()
    ctx["skip_featured_destinations"] = bool(dests)
    return render(request, "website/about.html", ctx)


def contact(request):
    page = get_site_page(SitePage.PageKey.CONTACT)
    initial = {
        "source_page": SitePage.PageKey.CONTACT,
        "next": reverse("contact"),
    }
    if request.user.is_authenticated:
        u = request.user
        initial["name"] = u.get_full_name() or u.get_username()
        initial["email"] = u.email
        if hasattr(u, "profile"):
            initial["phone"] = u.profile.phone
    form = LeadForm(initial=initial)
    return render(
        request,
        "website/contact.html",
        {"site_page": page, "lead_form": form},
    )


def faqs(request):
    ctx = _cms_context(SitePage.PageKey.FAQS, show_lead=False)
    return render(request, "website/faqs.html", ctx)


def legal(request):
    ctx = _cms_context(SitePage.PageKey.LEGAL, show_lead=False)
    return render(request, "website/legal.html", ctx)


_INVALID_LEAD_TEMPLATES = {
    SitePage.PageKey.HOME: "website/home.html",
    SitePage.PageKey.ABOUT: "website/about.html",
    SitePage.PageKey.CONTACT: "website/contact.html",
    SitePage.PageKey.FAQS: "website/faqs.html",
    SitePage.PageKey.LEGAL: "website/legal.html",
}


@require_POST
def lead_submit(request):
    form = LeadForm(request.POST)
    next_url = safe_next(request)
    if form.is_valid():
        lead = form.save(commit=False)
        if request.user.is_authenticated:
            lead.user = request.user
        lead.save()
        messages.success(request, "Thanks — we'll be in touch soon.")
        return HttpResponseRedirect(next_url)
    messages.error(request, "Please correct the errors below.")
    source = (form.data.get("source_page") or "").strip() or SitePage.PageKey.CONTACT
    valid_keys = {k for k, _ in SitePage.PageKey.choices}
    page_key = source if source in valid_keys else SitePage.PageKey.CONTACT
    template = _INVALID_LEAD_TEMPLATES.get(
        page_key, "website/contact.html"
    )
    if page_key == SitePage.PageKey.HOME:
        return _render_home_with_form(request, form)
    site_page = get_site_page(page_key)
    return render(
        request,
        template,
        {"site_page": site_page, "lead_form": form},
    )


def _render_home_with_form(request, form):
    """Re-render home with validation errors (same context as home())."""
    site_settings = SiteSettings.load()
    home_cfg = HomePageConfig.load()
    ctx = _cms_context(SitePage.PageKey.HOME, show_lead=False)
    ctx["lead_form"] = form
    ctx["home_cfg"] = home_cfg
    ctx["hero_image_url"] = (
        home_cfg.hero_image_url
        or site_settings.default_hero_image_url
        or _DEFAULT_HERO
    )
    lim = home_cfg.home_destinations_limit or 8
    pinned = Destination.objects.filter(show_on_homepage=True).order_by(
        "homepage_order", "name"
    )
    if pinned.exists():
        dests = list(pinned[:lim])
    else:
        dests = list(Destination.objects.order_by("name")[:lim])
    nfb = len(_FALLBACK_CARD_IMAGES)
    default_card = site_settings.default_card_image_url
    ctx["destination_showcase"] = [
        (
            d,
            (d.listing_image_url or default_card or _FALLBACK_CARD_IMAGES[i % nfb]),
        )
        for i, d in enumerate(dests)
    ]
    blog_n = home_cfg.blog_cards_limit or 4
    ctx["home_blog_posts"] = list(
        BlogPost.objects.order_by("-published_at", "title")[:blog_n]
    )
    ctx["hero_icon_features"] = list(
        HomeIconFeature.objects.filter(
            section=HomeIconFeature.Section.HERO_OVERLAY,
            is_active=True,
        ).order_by("sort_order")
    )
    ctx["sky_icon_features"] = list(
        HomeIconFeature.objects.filter(
            section=HomeIconFeature.Section.SKY_STRIP,
            is_active=True,
        ).order_by("sort_order")
    )
    ctx["promise_icon_features"] = list(
        HomeIconFeature.objects.filter(
            section=HomeIconFeature.Section.PROMISE,
            is_active=True,
        ).order_by("sort_order")
    )
    ctx["testimonials"] = _testimonials_for_home()
    ctx["gallery_images"] = list(
        GalleryImage.objects.filter(is_active=True).order_by("sort_order")[:12]
    )
    ctx["expert_bullets"] = list(
        home_cfg.expert_bullets.order_by("sort_order")
    )
    return render(request, "website/home.html", ctx)


def page_not_found(request, exception):
    return render(request, "website/404.html", status=404)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /leads/submit/",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
