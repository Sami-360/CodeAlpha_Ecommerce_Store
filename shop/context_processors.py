from django.db.models import Sum

from .models import CartItem, Wishlist


def cart_item_count(request):
    if not request.user.is_authenticated:
        return {
            "cart_item_count": 0,
            "wishlist_item_count": 0,
            "cart_count": 0,
            "wishlist_count": 0,
        }

    cart_count = (
        CartItem.objects.filter(user=request.user).aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return {
        "cart_item_count": cart_count,
        "wishlist_item_count": wishlist_count,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
    }
