from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Attraction,
    AttractionGalleryImage,
    BlogPost,
    Cart,
    CartItem,
    CategoryGalleryImage,
    Destination,
    DestinationCategory,
    ExpertBullet,
    FooterNavLink,
    FooterTrustBadge,
    GalleryImage,
    HomeIconFeature,
    HomePageConfig,
    Lead,
    PressMention,
    SitePage,
    SiteSettings,
    SocialLink,
    Testimonial,
    ThingToDo,
    ThingToDoGalleryImage,
    Tour,
    TourGalleryImage,
    UserProfile,
)


def _tagging_admin_html(*, blog_filter_kw, testimonial_filter_kw, obj_pk):
    """filter_kw like {"related_tours": obj} — single key for admin changelist."""
    if not obj_pk:
        return "—"
    key = next(iter(blog_filter_kw))
    param = {
        "related_tours": "related_tours__id__exact",
        "related_categories": "related_categories__id__exact",
        "related_attractions": "related_attractions__id__exact",
        "related_things_to_do": "related_things_to_do__id__exact",
    }[key]
    q = f"?{param}={obj_pk}"
    b_count = BlogPost.objects.filter(**blog_filter_kw).count()
    t_count = Testimonial.objects.filter(**testimonial_filter_kw).count()
    blog_url = reverse("admin:website_blogpost_changelist") + q
    tst_url = reverse("admin:website_testimonial_changelist") + q
    blog_bit = (
        format_html('<a href="{}">{} blog posts</a>', blog_url, b_count)
        if b_count
        else format_html("{} blog posts", b_count)
    )
    tst_bit = (
        format_html('<a href="{}">{} testimonials</a>', tst_url, t_count)
        if t_count
        else format_html("{} testimonials", t_count)
    )
    return format_html("{} · {}", blog_bit, tst_bit)


class DestinationCategoryInline(admin.TabularInline):
    model = DestinationCategory
    extra = 0
    fields = ("name", "slug", "summary")


class CategoryGalleryImageInline(admin.TabularInline):
    model = CategoryGalleryImage
    extra = 1


class TourGalleryImageInline(admin.TabularInline):
    model = TourGalleryImage
    extra = 1


class AttractionGalleryImageInline(admin.TabularInline):
    model = AttractionGalleryImage
    extra = 1


class ThingToDoGalleryImageInline(admin.TabularInline):
    model = ThingToDoGalleryImage
    extra = 1


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "show_on_homepage", "homepage_order")
    list_filter = ("show_on_homepage",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DestinationCategoryInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "summary")}),
        (
            "Homepage & media",
            {
                "fields": ("listing_image_url", "show_on_homepage", "homepage_order"),
            },
        ),
    )


@admin.register(DestinationCategory)
class DestinationCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "destination")
    list_filter = ("destination",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "summary")
    inlines = [CategoryGalleryImageInline]
    readonly_fields = ("cms_tagging_summary",)
    fieldsets = (
        (None, {"fields": ("destination", "name", "slug", "summary")}),
        (
            "CMS tagging visibility",
            {
                "description": "Blog posts and testimonials that tag this category (or tours inside it) use separate fields on those models.",
                "fields": ("cms_tagging_summary",),
            },
        ),
    )

    def cms_tagging_summary(self, obj):
        return _tagging_admin_html(
            blog_filter_kw={"related_categories": obj},
            testimonial_filter_kw={"related_categories": obj},
            obj_pk=obj.pk,
        )

    cms_tagging_summary.short_description = "Tagged in blog & reviews"


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "destination",
        "category",
        "price_from",
        "currency",
        "rating_average",
        "review_count",
        "duration_hours",
    )
    search_fields = ("name", "slug", "destination__name")
    list_filter = ("destination", "category", "free_cancellation", "skip_the_line", "wheelchair_accessible")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TourGalleryImageInline]
    readonly_fields = ("cms_tagging_summary",)
    fieldsets = (
        (None, {"fields": ("destination", "category", "name", "slug", "listing_image_url")}),
        (
            "Booking & listing",
            {
                "fields": (
                    "price_from",
                    "currency",
                    "rating_average",
                    "review_count",
                    "duration_hours",
                    "group_size_max",
                    "languages",
                    "free_cancellation",
                    "skip_the_line",
                    "wheelchair_accessible",
                ),
            },
        ),
        ("Copy", {"fields": ("teaser", "body")}),
        (
            "CMS tagging visibility",
            {
                "description": "Link this tour from Blog posts and Testimonials using their cross-link fields.",
                "fields": ("cms_tagging_summary",),
            },
        ),
    )

    def cms_tagging_summary(self, obj):
        return _tagging_admin_html(
            blog_filter_kw={"related_tours": obj},
            testimonial_filter_kw={"related_tours": obj},
            obj_pk=obj.pk,
        )

    cms_tagging_summary.short_description = "Tagged in blog & reviews"


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "destination")
    list_filter = ("destination",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttractionGalleryImageInline]
    readonly_fields = ("cms_tagging_summary",)
    fieldsets = (
        (None, {"fields": ("destination", "name", "slug", "summary", "body")}),
        (
            "CMS tagging visibility",
            {
                "description": "Tag this sight from Blog posts and Testimonials.",
                "fields": ("cms_tagging_summary",),
            },
        ),
    )

    def cms_tagging_summary(self, obj):
        return _tagging_admin_html(
            blog_filter_kw={"related_attractions": obj},
            testimonial_filter_kw={"related_attractions": obj},
            obj_pk=obj.pk,
        )

    cms_tagging_summary.short_description = "Tagged in blog & reviews"


@admin.register(ThingToDo)
class ThingToDoAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "destination")
    list_filter = ("destination",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ThingToDoGalleryImageInline]
    readonly_fields = ("cms_tagging_summary",)
    fieldsets = (
        (None, {"fields": ("destination", "name", "slug", "summary", "body")}),
        (
            "CMS tagging visibility",
            {
                "description": "Tag this activity from Blog posts and Testimonials.",
                "fields": ("cms_tagging_summary",),
            },
        ),
    )

    def cms_tagging_summary(self, obj):
        return _tagging_admin_html(
            blog_filter_kw={"related_things_to_do": obj},
            testimonial_filter_kw={"related_things_to_do": obj},
            obj_pk=obj.pk,
        )

    cms_tagging_summary.short_description = "Tagged in blog & reviews"


class ExpertBulletInline(admin.TabularInline):
    model = ExpertBullet
    extra = 0


@admin.register(HomePageConfig)
class HomePageConfigAdmin(admin.ModelAdmin):
    inlines = [ExpertBulletInline]
    fieldsets = (
        (
            "Hero",
            {
                "fields": (
                    "hero_image_url",
                    "hero_kicker",
                    "hero_intro_fallback",
                    "hero_cta_primary_label",
                    "hero_cta_primary_link",
                    "hero_cta_secondary_label",
                    "hero_cta_secondary_link",
                )
            },
        ),
        (
            "Destinations grid",
            {
                "fields": (
                    "destinations_kicker",
                    "destinations_title",
                    "destinations_empty_cta_label",
                    "destinations_view_all_label",
                    "home_destinations_limit",
                )
            },
        ),
        (
            "Video",
            {
                "fields": (
                    "video_enabled",
                    "video_title",
                    "video_subtitle",
                    "video_poster_url",
                    "video_watch_url",
                )
            },
        ),
        (
            "Community gallery",
            {
                "fields": (
                    "community_title",
                    "community_subtitle",
                    "community_hashtag",
                    "community_follow_label",
                    "community_follow_url",
                )
            },
        ),
        (
            "Testimonials",
            {
                "fields": (
                    "testimonial_section_title",
                    "testimonial_footer_note",
                )
            },
        ),
        (
            "Promise",
            {
                "fields": (
                    "promise_section_title",
                    "promise_section_subtitle",
                )
            },
        ),
        (
            "Expert block",
            {
                "fields": (
                    "expert_title",
                    "expert_body",
                    "expert_image_url",
                    "expert_image_alt",
                    "expert_cta_label",
                    "expert_cta_link",
                )
            },
        ),
        (
            "Blog strip",
            {
                "fields": (
                    "blog_section_title",
                    "blog_section_subtitle",
                    "blog_view_more_label",
                    "blog_cards_limit",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not HomePageConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "scope",
        "country_slug",
        "city_slug",
        "published_at",
    )
    list_filter = ("scope",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = (
        "related_destinations",
        "related_tours",
        "related_categories",
        "related_attractions",
        "related_things_to_do",
        "related_posts",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "listing_image_url",
                    "scope",
                    "country_slug",
                    "city_slug",
                    "excerpt",
                    "body",
                    "published_at",
                )
            },
        ),
        (
            "Cross-links",
            {
                "description": "Tag destinations, tours, categories, attractions, and things to do — they appear on those public pages as related stories. Link related posts for “read next”.",
                "fields": (
                    "related_destinations",
                    "related_tours",
                    "related_categories",
                    "related_attractions",
                    "related_things_to_do",
                    "related_posts",
                ),
            },
        ),
    )


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
    list_display = ("title", "page_key", "show_lead_form")
    list_filter = ("page_key",)
    filter_horizontal = (
        "featured_destinations",
        "featured_blog_posts",
        "featured_tours",
        "featured_attractions",
        "featured_things_to_do",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "page_key",
                    "title",
                    "intro",
                    "body",
                    "show_lead_form",
                )
            },
        ),
        (
            "Tagged content",
            {
                "description": "Show destinations, blog posts, tours, attractions, and things to do on this page.",
                "fields": (
                    "featured_destinations",
                    "featured_blog_posts",
                    "featured_tours",
                    "featured_attractions",
                    "featured_things_to_do",
                ),
            },
        ),
    )


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("tour",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "updated_at", "_item_count")
    list_filter = ("updated_at",)
    search_fields = ("session_key", "user__email", "user__username")
    readonly_fields = ("updated_at",)
    inlines = [CartItemInline]
    raw_id_fields = ("user",)

    def _item_count(self, obj):
        return obj.items.count()

    _item_count.short_description = "Items"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "country", "updated_at")
    search_fields = ("user__email", "user__username", "phone", "country")
    raw_id_fields = ("user",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "source_page",
        "user",
        "related_tour",
        "destination_interest",
        "created_at",
    )
    list_filter = ("source_page", "created_at")
    readonly_fields = ("created_at",)
    search_fields = ("name", "email", "message")
    raw_id_fields = ("user", "related_tour")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Brand",
            {"fields": ("site_name",)},
        ),
        (
            "Header",
            {
                "fields": (
                    "search_placeholder",
                    "header_account_url",
                    "header_cart_url",
                    "header_locale_label",
                )
            },
        ),
        (
            "Media fallbacks",
            {
                "fields": (
                    "default_hero_image_url",
                    "default_card_image_url",
                )
            },
        ),
        (
            "Footer newsletter",
            {
                "fields": (
                    "newsletter_title",
                    "newsletter_subtitle",
                    "newsletter_fine_print",
                )
            },
        ),
        (
            "Footer misc",
            {
                "fields": (
                    "footer_payment_line",
                    "press_bar_intro",
                    "copyright_holder",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HomeIconFeature)
class HomeIconFeatureAdmin(admin.ModelAdmin):
    list_display = ("section", "title", "icon", "sort_order", "is_active")
    list_filter = ("section", "is_active")
    list_editable = ("sort_order", "is_active")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("author", "rating", "sort_order", "is_active")
    list_filter = ("is_active",)
    list_editable = ("sort_order", "is_active")
    filter_horizontal = (
        "related_categories",
        "related_tours",
        "related_attractions",
        "related_things_to_do",
    )
    fieldsets = (
        (
            None,
            {"fields": ("quote", "author", "rating", "sort_order", "is_active")},
        ),
        (
            "Show on these pages",
            {
                "description": "Leave empty to use this quote only where global testimonials appear (e.g. home). "
                "Tag specific items to show it on those category, tour, attraction, or activity pages.",
                "fields": (
                    "related_categories",
                    "related_tours",
                    "related_attractions",
                    "related_things_to_do",
                ),
            },
        ),
    )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("alt_text", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")


@admin.register(FooterNavLink)
class FooterNavLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "column", "href", "sort_order")
    list_filter = ("column",)
    list_editable = ("sort_order",)


@admin.register(FooterTrustBadge)
class FooterTrustBadgeAdmin(admin.ModelAdmin):
    list_display = ("label", "sort_order")
    list_editable = ("sort_order",)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("network", "url", "sort_order")
    list_editable = ("sort_order",)


@admin.register(PressMention)
class PressMentionAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    list_editable = ("sort_order",)
