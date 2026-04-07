from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .cart import add_tour_to_cart, get_or_create_cart, merge_session_cart_into_user
from .forms import EmailLoginForm, TravelerSignUpForm, UserProfileDetailsForm
from .models import CartItem, Lead, Tour


def account_entry(request):
    """Landing at /account/: send signed-in users to profile, others to login."""
    if request.user.is_authenticated:
        return redirect("account_profile")
    return redirect("account_login")


def _safe_next_url(request):
    n = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if not n:
        return None
    if url_has_allowed_host_and_scheme(
        n,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return n
    return None


class AccountLoginView(LoginView):
    form_class = EmailLoginForm
    template_name = "website/account/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or reverse("account_profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        merge_session_cart_into_user(self.request, self.request.user)
        return response


account_logout = LogoutView.as_view(
    next_page=reverse_lazy("home"),
    http_method_names=["post", "options"],
)


@require_http_methods(["GET", "POST"])
def account_signup(request):
    if request.user.is_authenticated:
        return redirect("account_profile")
    if request.method == "POST":
        form = TravelerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            merge_session_cart_into_user(request, user)
            messages.success(request, "Welcome — your account is ready.")
            nxt = _safe_next_url(request)
            return redirect(nxt or reverse("account_profile"))
    else:
        form = TravelerSignUpForm()
    return render(request, "website/account/signup.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def account_profile(request):
    profile = request.user.profile
    if request.method == "POST":
        user_form = UserProfileDetailsForm(
            request.POST,
            instance=request.user,
            profile_instance=profile,
        )
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Profile updated.")
            return redirect("account_profile")
    else:
        user_form = UserProfileDetailsForm(
            instance=request.user,
            profile_instance=profile,
        )
    return render(
        request,
        "website/account/profile.html",
        {"user_form": user_form},
    )


@login_required
def account_cart(request):
    cart = get_or_create_cart(request)
    items = (
        cart.items.select_related("tour", "tour__destination")
        .order_by("tour__name")
        .all()
    )
    return render(
        request,
        "website/account/cart.html",
        {"cart": cart, "cart_items": items},
    )


@login_required
def account_inquiries(request):
    qs = Lead.objects.filter(user=request.user).select_related(
        "destination_interest", "related_tour", "related_tour__destination"
    )
    return render(
        request,
        "website/account/inquiries.html",
        {"inquiries": qs},
    )


@login_required
@require_POST
def account_cart_add(request, tour_id):
    tour = get_object_or_404(Tour, pk=tour_id)
    qty = int(request.POST.get("quantity") or 1)
    add_tour_to_cart(request, tour, quantity=qty)
    messages.success(
        request,
        f"Added “{tour.name}” to your cart.",
    )
    next_url = request.POST.get("next") or tour.get_absolute_url()
    return HttpResponseRedirect(next_url)


@login_required
@require_POST
def account_cart_update(request):
    cart = get_or_create_cart(request)
    for key, val in request.POST.items():
        if not key.startswith("qty_"):
            continue
        try:
            item_id = int(key.removeprefix("qty_"))
        except ValueError:
            continue
        try:
            q = int(val)
        except (TypeError, ValueError):
            continue
        item = CartItem.objects.filter(pk=item_id, cart=cart).first()
        if not item:
            continue
        if q < 1:
            item.delete()
        else:
            item.quantity = min(20, q)
            item.save(update_fields=["quantity"])
    messages.success(request, "Cart updated.")
    return redirect("account_cart")


@login_required
@require_POST
def account_cart_remove(request, item_id):
    cart = get_or_create_cart(request)
    CartItem.objects.filter(pk=item_id, cart=cart).delete()
    messages.info(request, "Removed from cart.")
    return redirect("account_cart")
