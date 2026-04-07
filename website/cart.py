from django.db.models import Sum

from .models import Cart, CartItem


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def cart_item_count_for_request(request):
    total = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            total = cart.items.aggregate(s=Sum("quantity"))["s"] or 0
    elif request.session.session_key:
        cart = Cart.objects.filter(
            user__isnull=True, session_key=request.session.session_key
        ).first()
        if cart:
            total = cart.items.aggregate(s=Sum("quantity"))["s"] or 0
    return total


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            defaults={"session_key": None},
        )
        if cart.session_key:
            cart.session_key = None
            cart.save(update_fields=["session_key", "updated_at"])
        return cart
    sk = _ensure_session_key(request)
    cart, _ = Cart.objects.get_or_create(
        user=None,
        session_key=sk,
        defaults={},
    )
    return cart


def merge_session_cart_into_user(request, user):
    if not request.session.session_key:
        return
    session_cart = Cart.objects.filter(
        user__isnull=True, session_key=request.session.session_key
    ).first()
    if not session_cart or not session_cart.items.exists():
        session_cart.delete() if session_cart else None
        return
    user_cart, _ = Cart.objects.get_or_create(user=user, defaults={"session_key": None})
    if user_cart.session_key:
        user_cart.session_key = None
        user_cart.save(update_fields=["session_key", "updated_at"])
    for item in list(session_cart.items.all()):
        other = CartItem.objects.filter(cart=user_cart, tour=item.tour).first()
        if other:
            other.quantity += item.quantity
            other.save(update_fields=["quantity"])
            item.delete()
        else:
            item.cart = user_cart
            item.save(update_fields=["cart"])
    session_cart.delete()


def add_tour_to_cart(request, tour, quantity=1):
    cart = get_or_create_cart(request)
    quantity = max(1, min(int(quantity), 20))
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        tour=tour,
        defaults={"quantity": quantity},
    )
    if not created:
        item.quantity = min(20, item.quantity + quantity)
        item.save(update_fields=["quantity"])
    return item
