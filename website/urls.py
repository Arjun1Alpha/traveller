from django.urls import include, path

from . import account_views, views

account_urlpatterns = [
    path("", account_views.account_entry, name="account_home"),
    path("login/", account_views.AccountLoginView.as_view(), name="account_login"),
    path("logout/", account_views.account_logout, name="account_logout"),
    path("signup/", account_views.account_signup, name="account_signup"),
    path("profile/", account_views.account_profile, name="account_profile"),
    path("inquiries/", account_views.account_inquiries, name="account_inquiries"),
]

cart_urlpatterns = [
    path("", account_views.account_cart, name="account_cart"),
    path(
        "add/<int:tour_id>/",
        account_views.account_cart_add,
        name="account_cart_add",
    ),
    path("update/", account_views.account_cart_update, name="account_cart_update"),
    path(
        "remove/<int:item_id>/",
        account_views.account_cart_remove,
        name="account_cart_remove",
    ),
]

urlpatterns = [
    # Legacy /account/cart/… URLs (still work for old links and cached forms)
    path("account/cart/", account_views.account_cart),
    path(
        "account/cart/add/<int:tour_id>/",
        account_views.account_cart_add,
    ),
    path("account/cart/update/", account_views.account_cart_update),
    path(
        "account/cart/remove/<int:item_id>/",
        account_views.account_cart_remove,
    ),
    path("account/", include(account_urlpatterns)),
    path("cart/", include(cart_urlpatterns)),
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("destinations/", views.destination_list, name="destination_list"),
    path(
        "destinations/<slug:dest_slug>/",
        views.destination_hub,
        name="destination_hub",
    ),
    path(
        "destinations/<slug:dest_slug>/categories/",
        views.destination_categories,
        name="destination_categories",
    ),
    path(
        "destinations/<slug:dest_slug>/categories/<slug:cat_slug>/",
        views.destination_category_detail,
        name="destination_category_detail",
    ),
    path(
        "destinations/<slug:dest_slug>/tours/",
        views.tour_list,
        name="tour_list",
    ),
    path(
        "destinations/<slug:dest_slug>/tours/<slug:tour_slug>/",
        views.tour_pdp,
        name="tour_pdp",
    ),
    path(
        "destinations/<slug:dest_slug>/tours/<slug:tour_slug>/inquiry/",
        views.tour_inquiry_submit,
        name="tour_inquiry_submit",
    ),
    path(
        "destinations/<slug:dest_slug>/attractions/<slug:attraction_slug>/",
        views.attraction_detail,
        name="attraction_detail",
    ),
    path(
        "destinations/<slug:dest_slug>/attractions/",
        views.destination_attractions,
        name="destination_attractions",
    ),
    path(
        "destinations/<slug:dest_slug>/things-to-do/<slug:thing_slug>/",
        views.thing_to_do_detail,
        name="thing_to_do_detail",
    ),
    path(
        "destinations/<slug:dest_slug>/things-to-do/",
        views.destination_things_to_do,
        name="destination_things_to_do",
    ),
    path("blog/", views.blog_index, name="blog_index"),
    path(
        "blog/country/<slug:country_slug>/",
        views.blog_country,
        name="blog_country",
    ),
    path(
        "blog/city/<slug:city_slug>/",
        views.blog_city,
        name="blog_city",
    ),
    path(
        "blog/post/<slug:post_slug>/",
        views.blog_post_detail,
        name="blog_post_detail",
    ),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("faqs/", views.faqs, name="faqs"),
    path("legal/", views.legal, name="legal"),
    path("leads/submit/", views.lead_submit, name="lead_submit"),
]
