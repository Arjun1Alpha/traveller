from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class SitePage(models.Model):
    """CMS-backed content for fixed routes (home, about, contact, faqs, legal)."""

    class PageKey(models.TextChoices):
        HOME = "home", "Home"
        ABOUT = "about", "About"
        CONTACT = "contact", "Contact"
        FAQS = "faqs", "FAQs"
        LEGAL = "legal", "Legal"

    page_key = models.CharField(
        max_length=20,
        choices=PageKey.choices,
        unique=True,
    )
    title = models.CharField(max_length=200)
    intro = models.TextField(
        blank=True,
        help_text="Short text below the title (plain text).",
    )
    body = models.TextField(
        blank=True,
        help_text="Main copy (plain text; line breaks preserved on the site).",
    )
    show_lead_form = models.BooleanField(
        default=False,
        help_text="If enabled, the lead capture form appears on this page (in addition to Contact).",
    )
    featured_destinations = models.ManyToManyField(
        "Destination",
        blank=True,
        related_name="featured_on_pages",
        help_text="Pinned destinations with quick links to hub and sub-pages.",
    )
    featured_blog_posts = models.ManyToManyField(
        "BlogPost",
        blank=True,
        related_name="featured_on_pages",
    )
    featured_tours = models.ManyToManyField(
        "Tour",
        blank=True,
        related_name="featured_on_pages",
    )
    featured_attractions = models.ManyToManyField(
        "Attraction",
        blank=True,
        related_name="featured_on_pages",
    )
    featured_things_to_do = models.ManyToManyField(
        "ThingToDo",
        blank=True,
        related_name="featured_on_pages",
    )

    class Meta:
        ordering = ["page_key"]

    def __str__(self):
        return self.get_page_key_display()


class Lead(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField(blank=True)
    destination_interest = models.ForeignKey(
        "Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        help_text="Set when the visitor was signed in.",
    )
    related_tour = models.ForeignKey(
        "Tour",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        help_text="Tour this message refers to, if any.",
    )
    source_page = models.CharField(
        max_length=40,
        blank=True,
        help_text="Page key or path the visitor submitted from.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Destination(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, max_length=120)
    summary = models.TextField(blank=True)
    listing_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional image for destination cards on the home page.",
    )
    show_on_homepage = models.BooleanField(
        default=False,
        help_text="If checked, this destination is prioritized on the home grid (ordered below).",
    )
    homepage_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first among homepage destinations.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("destination_hub", kwargs={"dest_slug": self.slug})


class DestinationCategory(models.Model):
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    summary = models.TextField(
        blank=True,
        help_text="Optional short blurb for category cards and hub chips.",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["destination", "slug"],
                name="website_destcategory_dest_slug_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.destination.name}: {self.name}"

    def get_absolute_url(self):
        return reverse(
            "destination_category_detail",
            kwargs={"dest_slug": self.destination.slug, "cat_slug": self.slug},
        )


class Tour(models.Model):
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="tours"
    )
    category = models.ForeignKey(
        DestinationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tours",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=160)
    teaser = models.TextField(blank=True)
    body = models.TextField(blank=True)
    listing_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional thumbnail for tour cards and listings.",
    )
    price_from = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Lowest typical adult price per person (empty = ask us).",
    )
    currency = models.CharField(
        max_length=3,
        default="EUR",
        help_text="ISO 4217 code shown with price (e.g. EUR, GBP, USD).",
    )
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("4.70"),
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("5")),
        ],
        help_text="Display rating 0–5 (e.g. from partner surveys).",
    )
    review_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of reviews this rating is based on.",
    )
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("2.50"),
        validators=[MinValueValidator(Decimal("0.25"))],
        help_text="Typical guided time in hours.",
    )
    group_size_max = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Maximum guests per departure (empty if it varies).",
    )
    languages = models.CharField(
        max_length=200,
        blank=True,
        help_text="Languages offered, comma-separated (searchable on tour lists).",
    )
    free_cancellation = models.BooleanField(
        default=True,
        help_text="Show free-cancellation badge when true.",
    )
    skip_the_line = models.BooleanField(
        default=False,
        help_text="Priority / timed entry or skip-the-line style access.",
    )
    wheelchair_accessible = models.BooleanField(
        default=False,
        help_text="Marketed as wheelchair-friendly (partial or full).",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["destination", "slug"],
                name="website_tour_dest_slug_uniq",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "tour_pdp",
            kwargs={"dest_slug": self.destination.slug, "tour_slug": self.slug},
        )


class Attraction(models.Model):
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="attractions"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=160)
    summary = models.TextField(blank=True)
    body = models.TextField(
        blank=True,
        help_text="Optional longer copy for the attraction detail page.",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["destination", "slug"],
                name="website_attraction_dest_slug_uniq",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "attraction_detail",
            kwargs={
                "dest_slug": self.destination.slug,
                "attraction_slug": self.slug,
            },
        )


class ThingToDo(models.Model):
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="things_to_do"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=160)
    summary = models.TextField(blank=True)
    body = models.TextField(
        blank=True,
        help_text="Optional longer copy for the activity detail page.",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["destination", "slug"],
                name="website_thingtodo_dest_slug_uniq",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "thing_to_do_detail",
            kwargs={"dest_slug": self.destination.slug, "thing_slug": self.slug},
        )


class CategoryGalleryImage(models.Model):
    category = models.ForeignKey(
        DestinationCategory,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "category gallery image"
        verbose_name_plural = "category gallery images"

    def __str__(self):
        return self.alt_text or self.image_url[:40]


class TourGalleryImage(models.Model):
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "tour gallery image"
        verbose_name_plural = "tour gallery images"

    def __str__(self):
        return self.alt_text or self.image_url[:40]


class AttractionGalleryImage(models.Model):
    attraction = models.ForeignKey(
        Attraction,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "attraction gallery image"
        verbose_name_plural = "attraction gallery images"

    def __str__(self):
        return self.alt_text or self.image_url[:40]


class ThingToDoGalleryImage(models.Model):
    thing_to_do = models.ForeignKey(
        ThingToDo,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "thing to do gallery image"
        verbose_name_plural = "thing to do gallery images"

    def __str__(self):
        return self.alt_text or self.image_url[:40]


class BlogPost(models.Model):
    class Scope(models.TextChoices):
        COUNTRY = "country", "Country"
        CITY = "city", "City"
        GENERAL = "general", "General"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=160)
    scope = models.CharField(
        max_length=20, choices=Scope.choices, default=Scope.GENERAL
    )
    country_slug = models.SlugField(
        max_length=120,
        blank=True,
        help_text="Used for /blog/country/<slug>/ when scope is Country.",
    )
    city_slug = models.SlugField(
        max_length=120,
        blank=True,
        help_text="Used for /blog/city/<slug>/ when scope is City.",
    )
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    listing_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Thumbnail for blog listings (home, index). Falls back to site default if empty.",
    )
    related_destinations = models.ManyToManyField(
        "Destination",
        blank=True,
        related_name="blog_posts_tagged",
        help_text="Destinations this article is associated with (shown on those hub pages).",
    )
    related_tours = models.ManyToManyField(
        "Tour",
        blank=True,
        related_name="blog_posts_tagged",
        help_text="Tours (PDPs) to highlight from this post.",
    )
    related_categories = models.ManyToManyField(
        "DestinationCategory",
        blank=True,
        related_name="tagged_blog_posts",
        help_text="Category pages that should surface this article.",
    )
    related_attractions = models.ManyToManyField(
        "Attraction",
        blank=True,
        related_name="tagged_blog_posts",
        help_text="Attraction detail pages that should surface this article.",
    )
    related_things_to_do = models.ManyToManyField(
        "ThingToDo",
        blank=True,
        related_name="tagged_blog_posts",
        help_text="Things-to-do detail pages that should surface this article.",
    )
    related_posts = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="linked_from_posts",
        help_text="Other blog posts to surface as related reading.",
    )

    class Meta:
        ordering = ["-published_at", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_post_detail", kwargs={"post_slug": self.slug})


class SiteSettings(models.Model):
    """Global branding, header, footer, and fallbacks (single row — pk=1)."""

    site_name = models.CharField(max_length=120, default="Traveler")
    search_placeholder = models.CharField(
        max_length=160,
        default="Where do you want to go?",
    )
    header_account_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Leave blank to use this site’s /account/ (recommended). If set, an extra “External account” link appears in the header only.",
    )
    header_cart_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Leave blank to use this site’s /cart/ (recommended). If set, an extra “External cart” link appears in the header only.",
    )
    header_locale_label = models.CharField(max_length=80, default="EN · USD", blank=True)
    default_hero_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Used when the home hero URL is empty.",
    )
    default_card_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Fallback for blog/destination cards without an image.",
    )
    newsletter_title = models.CharField(max_length=200, default="Get travel inspiration")
    newsletter_subtitle = models.CharField(max_length=300, blank=True)
    newsletter_fine_print = models.CharField(max_length=300, blank=True)
    footer_payment_line = models.CharField(max_length=200, blank=True)
    press_bar_intro = models.CharField(max_length=120, default="As seen in", blank=True)
    copyright_holder = models.CharField(max_length=200, default="Traveler", blank=True)

    class Meta:
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomePageConfig(models.Model):
    """Home page copy and section settings (single row — pk=1)."""

    hero_image_url = models.URLField(max_length=500, blank=True)
    hero_kicker = models.CharField(max_length=120, default="Experience more", blank=True)
    hero_intro_fallback = models.TextField(
        blank=True,
        help_text="Shown under the title when the Home SitePage intro is empty.",
    )
    hero_cta_primary_label = models.CharField(max_length=80, default="Explore destinations")
    hero_cta_primary_link = models.CharField(
        max_length=400,
        default="/destinations/",
        help_text="Path (e.g. /contact/) or full https URL.",
    )
    hero_cta_secondary_label = models.CharField(max_length=80, default="Plan a trip")
    hero_cta_secondary_link = models.CharField(
        max_length=400,
        default="/contact/",
        blank=True,
    )
    destinations_kicker = models.CharField(max_length=120, default="Signature experiences")
    destinations_title = models.CharField(max_length=200, default="Top destinations")
    destinations_empty_cta_label = models.CharField(
        max_length=120,
        default="Browse all destinations",
    )
    destinations_view_all_label = models.CharField(
        max_length=120,
        default="View all destinations",
    )
    home_destinations_limit = models.PositiveSmallIntegerField(default=8)
    video_enabled = models.BooleanField(default=True)
    video_title = models.CharField(max_length=200, default="Why choose our tours?")
    video_subtitle = models.CharField(max_length=400, blank=True)
    video_poster_url = models.URLField(max_length=500, blank=True)
    video_watch_url = models.URLField(max_length=500, blank=True)
    community_title = models.CharField(max_length=200, default="Join our global travel community")
    community_subtitle = models.TextField(blank=True)
    community_hashtag = models.CharField(max_length=80, default="#TravelerTours", blank=True)
    community_follow_label = models.CharField(max_length=80, default="Follow us")
    community_follow_url = models.URLField(max_length=500, blank=True)
    testimonial_section_title = models.CharField(max_length=200, default="Thousands of five-star reviews")
    testimonial_footer_note = models.CharField(max_length=300, blank=True)
    promise_section_title = models.CharField(max_length=200, default="The Traveler promise")
    promise_section_subtitle = models.TextField(blank=True)
    expert_title = models.CharField(max_length=200, default="Expert guides, every step")
    expert_body = models.TextField(blank=True)
    expert_image_url = models.URLField(max_length=500, blank=True)
    expert_image_alt = models.CharField(max_length=200, blank=True)
    expert_cta_label = models.CharField(max_length=80, default="Find a tour")
    expert_cta_link = models.CharField(max_length=400, default="/destinations/", blank=True)
    blog_section_title = models.CharField(max_length=200, default="Travel insights")
    blog_section_subtitle = models.CharField(max_length=300, blank=True)
    blog_view_more_label = models.CharField(max_length=80, default="View more")
    blog_cards_limit = models.PositiveSmallIntegerField(default=4)

    class Meta:
        verbose_name_plural = "Home page config"

    def __str__(self):
        return "Home page"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ExpertBullet(models.Model):
    home = models.ForeignKey(
        HomePageConfig,
        on_delete=models.CASCADE,
        related_name="expert_bullets",
    )
    text = models.CharField(max_length=300)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.text[:40]


class HomeIconFeature(models.Model):
    class Section(models.TextChoices):
        HERO_OVERLAY = "hero_overlay", "Hero (overlay bar)"
        SKY_STRIP = "sky_strip", "Sky strip (3 columns)"
        PROMISE = "promise", "Promise (3 columns)"

    section = models.CharField(max_length=20, choices=Section.choices)
    icon = models.CharField(
        max_length=80,
        help_text="Bootstrap Icons class, e.g. bi-star-fill (no leading dot).",
    )
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "sort_order", "id"]

    def __str__(self):
        return f"{self.section}: {self.title or self.icon}"


class Testimonial(models.Model):
    quote = models.TextField()
    author = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    related_categories = models.ManyToManyField(
        "DestinationCategory",
        blank=True,
        related_name="tagged_testimonials",
        help_text="Show this quote on those category pages (in addition to global rules).",
    )
    related_tours = models.ManyToManyField(
        "Tour",
        blank=True,
        related_name="tagged_testimonials",
        help_text="Show on matching tour detail pages.",
    )
    related_attractions = models.ManyToManyField(
        "Attraction",
        blank=True,
        related_name="tagged_testimonials",
        help_text="Show on matching attraction detail pages.",
    )
    related_things_to_do = models.ManyToManyField(
        "ThingToDo",
        blank=True,
        related_name="tagged_testimonials",
        help_text="Show on matching things-to-do detail pages.",
    )

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return (self.author or "Anonymous")[:50]


class GalleryImage(models.Model):
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.alt_text or self.image_url[:40]


class FooterNavLink(models.Model):
    class Column(models.TextChoices):
        COMPANY = "company", "Company"
        HELP = "help", "Help"

    column = models.CharField(max_length=20, choices=Column.choices)
    label = models.CharField(max_length=120)
    href = models.CharField(
        max_length=400,
        help_text="Path like /about/ or full URL.",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["column", "sort_order", "id"]

    def __str__(self):
        return f"{self.column}: {self.label}"


class FooterTrustBadge(models.Model):
    label = models.CharField(max_length=80)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.label


class SocialLink(models.Model):
    class Network(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        YOUTUBE = "youtube", "YouTube"
        TWITTER = "twitter", "X / Twitter"
        TIKTOK = "tiktok", "TikTok"

    network = models.CharField(max_length=20, choices=Network.choices)
    url = models.URLField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.get_network_display()

    def icon_bootstrap(self):
        m = {
            self.Network.INSTAGRAM: "bi-instagram",
            self.Network.FACEBOOK: "bi-facebook",
            self.Network.YOUTUBE: "bi-youtube",
            self.Network.TWITTER: "bi-twitter-x",
            self.Network.TIKTOK: "bi-tiktok",
        }
        return m.get(self.network, "bi-link-45deg")


class PressMention(models.Model):
    name = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=40, blank=True)
    country = models.CharField(max_length=80, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user}"


class Cart(models.Model):
    """One cart per signed-in user, or per anonymous session."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shopping_cart",
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False)
                | models.Q(session_key__isnull=False),
                name="website_cart_user_or_session",
            ),
            models.UniqueConstraint(
                fields=["session_key"],
                condition=models.Q(user__isnull=True),
                name="website_cart_session_key_uniq_anon",
            ),
        ]

    def __str__(self):
        if self.user_id:
            return f"Cart user={self.user_id}"
        return f"Cart session={self.session_key}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    tour = models.ForeignKey(
        "Tour",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "tour"],
                name="website_cartitem_cart_tour_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}× {self.tour.name}"
