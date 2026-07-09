from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
from datetime import timedelta

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Address,
    CartItem,
    ContactMessage,
    Coupon,
    NewsletterSubscriber,
    Order,
    OrderItem,
    Product,
    Review,
    UserProfile,
    Wishlist,
)
from .forms import CustomUserCreationForm


SORT_OPTIONS = [
    ("newest", "Newest"),
    ("price_low", "Price: Low to High"),
    ("price_high", "Price: High to Low"),
    ("name", "Name"),
]

SORT_ORDERING = {
    "price_low": ("price", "name"),
    "price_high": ("-price", "name"),
    "newest": ("-created_at", "-id"),
    "name": ("name",),
}

COUPON_SESSION_KEY = "applied_coupon_code"
TAX_RATE = Decimal("0.05")
SHIPPING_CHARGE = Decimal("200.00")
FREE_SHIPPING_THRESHOLD = Decimal("3000.00")
MONEY_QUANTIZER = Decimal("0.01")


def quantize_money(value):
    return Decimal(value).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def get_active_coupon(code):
    if not code:
        return None

    now = timezone.now()
    return Coupon.objects.filter(
        code=code.upper(),
        active=True,
        valid_from__lte=now,
        valid_until__gte=now,
        times_used__lt=F("usage_limit"),
    ).first()


def calculate_cart_pricing(items, coupon_code=None):
    subtotal = quantize_money(sum(item.get_total_item_price() for item in items))
    coupon = get_active_coupon(coupon_code)
    discount = Decimal("0.00")

    if coupon:
        discount = quantize_money(subtotal * Decimal(coupon.discount_percent) / Decimal("100"))

    discounted_subtotal = quantize_money(max(Decimal("0.00"), subtotal - discount))
    tax = quantize_money(discounted_subtotal * TAX_RATE)
    shipping = (
        Decimal("0.00")
        if discounted_subtotal >= FREE_SHIPPING_THRESHOLD or subtotal == Decimal("0.00")
        else SHIPPING_CHARGE
    )
    grand_total = quantize_money(discounted_subtotal + tax + shipping)

    return {
        "subtotal": subtotal,
        "coupon": coupon,
        "coupon_code": coupon.code if coupon else "",
        "discount": discount,
        "tax": tax,
        "shipping": shipping,
        "grand_total": grand_total,
    }


def pricing_json(pricing):
    return {
        "subtotal": pricing["subtotal"],
        "discount": pricing["discount"],
        "tax": pricing["tax"],
        "shipping": pricing["shipping"],
        "grand_total": pricing["grand_total"],
    }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("phone_number",)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("label", "full_address", "city")
        widgets = {
            "label": forms.TextInput(attrs={"placeholder": "e.g. Home, Office"}),
            "full_address": forms.Textarea(attrs={"rows": 3, "placeholder": "123 Main St"}),
            "city": forms.TextInput(attrs={"placeholder": "e.g. Karachi"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_form_control_class(self)


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_form_control_class(self)


class ShippingAddressForm(forms.Form):
    shipping_address_id = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        empty_label="--- Select a saved address ---",
        widget=forms.Select(attrs={"class": "form-select mb-3"}),
    )
    save_new_address = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["shipping_address_id"].queryset = get_user_addresses(user)

    def get_selected_address_text(self):
        address = self.cleaned_data.get("shipping_address_id")
        if address:
            return f"{address.full_address}, {address.city}"
        return None


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Share your experience with this product",
                }
            ),
        }


def add_form_control_class(form):
    for field in form.fields.values():
        existing_classes = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{existing_classes} form-control".strip()


def get_user_addresses(user):
    return Address.objects.filter(user=user)


LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_SECONDS = 60


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("product_list")
    else:
        form = CustomUserCreationForm()

    add_form_control_class(form)
    return render(request, "registration/register.html", {"form": form})




# Note: For a more robust rate-limiting solution, consider using a package like django-axes.
def login_view(request):
    lockout_until_ts = request.session.get("login_lockout_until")
    now = timezone.now()
    if lockout_until_ts and now.timestamp() < lockout_until_ts:
        remaining = int(lockout_until_ts - now.timestamp())
        form = AuthenticationForm(request)
        messages.error(
            request,
            f"Too many failed login attempts. Try again in {remaining} seconds.",
        )
        return render(request, "registration/login.html", {"form": form})

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session.pop("login_failed_attempts", None)
            request.session.pop("login_lockout_until", None)
            display_name = user.first_name or user.username
            messages.success(request, f"Welcome back, {display_name}!")
            if next_url:
                return redirect(next_url)
            return redirect("product_list")
        else:
            attempts = request.session.get("login_failed_attempts", 0) + 1
            request.session["login_failed_attempts"] = attempts
            if attempts >= LOGIN_MAX_FAILURES:
                lockout_until = now + timedelta(seconds=LOGIN_LOCKOUT_SECONDS)
                request.session["login_lockout_until"] = lockout_until.timestamp()
                messages.error(
                    request,
                    f"Too many failed login attempts. Try again in {LOGIN_LOCKOUT_SECONDS} seconds.",
                )
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)

    return render(request, "registration/login.html", {"form": form, "next": next_url})


def about(request):
    return render(request, "shop/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for contacting us. We will get back to you soon.")
            return redirect("contact")
    else:
        form = ContactMessageForm()

    return render(request, "shop/contact.html", {"form": form})


def privacy_policy(request):
    return render(request, "shop/privacy_policy.html")


def terms_of_service(request):
    return render(request, "shop/terms_of_service.html")


@require_POST
def newsletter_subscribe(request):
    email = request.POST.get("email", "").strip().lower()
    if not email:
        return JsonResponse({"success": False, "message": "Please enter an email address."}, status=400)

    NewsletterSubscriber.objects.get_or_create(email=email)
    return JsonResponse({"success": True, "message": "Thanks for subscribing!"})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("product_list")


@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    addresses = get_user_addresses(request.user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, instance=user_profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("profile")
        elif "add_address" in request.POST:
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                new_address = address_form.save(commit=False)
                new_address.user = request.user
                new_address.save()
                messages.success(request, "New address added.")
                return redirect("profile")
    else:
        profile_form = UserProfileForm(instance=user_profile)
        address_form = AddressForm()

    return render(
        request,
        "shop/profile.html",
        {
            "profile_form": profile_form,
            "address_form": address_form,
            "addresses": addresses,
        },
    )


@login_required
@require_POST
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if not address.is_default:
        address.delete()
        messages.success(request, "Address has been deleted.")
    else:
        messages.error(request, "You cannot delete your default address.")
    return redirect("profile")


@login_required
@require_POST
def set_default_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    with transaction.atomic():
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default"])
    messages.success(request, "Default address has been updated.")
    return redirect("profile")


def product_list(request):
    category = request.GET.get("category")
    search_query = request.GET.get("q", "").strip()
    selected_sort = request.GET.get("sort", "newest")
    if selected_sort not in SORT_ORDERING:
        selected_sort = "newest"

    cache_key = hashlib.md5(
        f"{category or ''}|{search_query}|{selected_sort}".encode("utf-8")
    ).hexdigest()
    products = cache.get(f"product_list:{cache_key}")
    if products is None:
        products = Product.objects.filter(stock__gt=0).prefetch_related("images")
        if category:
            products = products.filter(category=category)

        if search_query:
            products = products.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        products = products.order_by(*SORT_ORDERING[selected_sort])
        products = list(products)
        cache.set(f"product_list:{cache_key}", products, 60)

    wishlisted_product_ids = set()
    if request.user.is_authenticated:
        wishlisted_product_ids = set(
            Wishlist.objects.filter(user=request.user).values_list(
                "product_id", flat=True
            )
        )

    categories = (
        Product.objects.filter(stock__gt=0)
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    def build_query(**updates):
        query = request.GET.copy()
        for key, value in updates.items():
            if value in (None, ""):
                query.pop(key, None)
            else:
                query[key] = value
        return query.urlencode()

    sort_options = [
        {
            "value": value,
            "label": label,
            "url": f"?{build_query(sort=value, page=None)}",
        }
        for value, label in SORT_OPTIONS
    ]
    category_options = [
        {
            "name": item,
            "url": f"?{build_query(category=item, page=None)}",
            "selected": item == category,
        }
        for item in categories
    ]
    page_links = [
        {
            "number": page_number,
            "url": f"?{build_query(page=page_number)}",
            "active": page_number == page_obj.number,
        }
        for page_number in paginator.page_range
    ]

    return render(
        request,
        "shop/product_list.html",
        {
            "products": page_obj,
            "page_obj": page_obj,
            "result_count": paginator.count,
            "category_options": category_options,
            "all_categories_url": f"?{build_query(category=None, page=None)}",
            "sort_options": sort_options,
            "selected_sort": selected_sort,
            "selected_category": category,
            "search_query": search_query,
            "page_links": page_links,
            "previous_page_url": (
                f"?{build_query(page=page_obj.previous_page_number())}"
                if page_obj.has_previous()
                else ""
            ),
            "next_page_url": (
                f"?{build_query(page=page_obj.next_page_number())}"
                if page_obj.has_next()
                else ""
            ),
            "wishlisted_product_ids": wishlisted_product_ids,
        },
    )


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    gallery_images = product.images.all().order_by("-is_primary", "id")
    reviews = product.reviews.select_related("user").order_by("-created_at")
    rating_summary = reviews.aggregate(average_rating=Avg("rating"))
    user_has_reviewed = False
    is_wishlisted = False

    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(user=request.user).exists()
        is_wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()


    related_products = (
        Product.objects.filter(category=product.category, stock__gt=0)
        .exclude(pk=product.pk)
        .order_by("-created_at")[:4]
        if product.category
        else []
    )

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "gallery_images": gallery_images,
            "reviews": reviews,
            "average_rating": rating_summary["average_rating"],
            "review_count": reviews.count(),
            "review_form": ReviewForm(),
            "user_has_reviewed": user_has_reviewed,
            "related_products": related_products,
            "is_wishlisted": is_wishlisted,
        },
    )


@login_required
@require_POST
def add_review(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.error(request, "You have already reviewed this product.")
        return redirect("product_detail", pk=product.pk)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        try:
            review.save()
            messages.success(request, "Thanks for sharing your review.")
        except IntegrityError:
            messages.error(request, "You have already reviewed this product.")
    else:
        messages.error(request, "Please choose a rating and enter a review.")

    return redirect("product_detail", pk=product.pk)


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, stock__gt=0)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, quantity)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"quantity": quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=["quantity"])

    cart_count = (
        CartItem.objects.filter(user=request.user).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    return JsonResponse({"success": True, "cart_count": cart_count})


@login_required
def view_cart(request):
    items = CartItem.objects.filter(user=request.user).select_related("product")
    pricing = calculate_cart_pricing(items, request.session.get(COUPON_SESSION_KEY))
    return render(
        request,
        "shop/cart.html",
        {
            "items": items,
            "pricing": pricing,
            "total": pricing["grand_total"],
        },
    )


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get("coupon_code", "").strip().upper()

    if not code:
        request.session.pop(COUPON_SESSION_KEY, None)
        messages.info(request, "Coupon removed.")
        return redirect("view_cart")

    now = timezone.now()
    coupon = Coupon.objects.filter(code=code).first()

    if not coupon:
        messages.error(request, "Invalid coupon code.")
    elif not coupon.active:
        messages.error(request, "This coupon is not active.")
    elif coupon.valid_from > now or coupon.valid_until < now:
        messages.error(request, "This coupon is expired or not yet valid.")
    elif coupon.times_used >= coupon.usage_limit:
        messages.error(request, "This coupon has reached its usage limit.")
    else:
        request.session[COUPON_SESSION_KEY] = coupon.code
        messages.success(request, f"Coupon {coupon.code} applied.")

    return redirect("view_cart")


@login_required
@require_POST
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related("product"),
        pk=item_id,
        user=request.user,
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    cart_item.quantity = max(1, quantity)
    cart_item.save(update_fields=["quantity"])

    items = CartItem.objects.filter(user=request.user).select_related("product")
    pricing = calculate_cart_pricing(items, request.session.get(COUPON_SESSION_KEY))

    return JsonResponse(
        {
            "success": True,
            "item_total": cart_item.get_total_item_price(),
            "cart_total": pricing["grand_total"],
            "pricing": pricing_json(pricing),
        }
    )


@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, user=request.user)
    cart_item.delete()
    return redirect("view_cart")


from django.core.mail import send_mail


@login_required
def checkout(request):
    items = CartItem.objects.filter(user=request.user).select_related("product")
    pricing = calculate_cart_pricing(items, request.session.get(COUPON_SESSION_KEY))
    user_addresses = get_user_addresses(request.user)
    default_address = user_addresses.filter(is_default=True).first()

    if not items.exists():
        return render(request, "shop/checkout.html", {"items": items})

    if request.method == "POST":
        address_form = AddressForm(request.POST, prefix="new")
        shipping_form = ShippingAddressForm(request.POST, user=request.user, prefix="shipping")

        shipping_address_str = ""
        is_valid = False

        selected_address_id = request.POST.get("shipping-shipping_address_id")

        if selected_address_id:
            shipping_form.is_valid()
            selected_address = get_object_or_404(Address, pk=selected_address_id, user=request.user)
            shipping_address_str = f"{selected_address.full_address}, {selected_address.city}"
            is_valid = True
        elif address_form.is_valid():
            is_valid = True
            new_address = address_form.save(commit=False)
            shipping_address_str = f"{new_address.full_address}, {new_address.city}"

            if request.POST.get("shipping-save_new_address"):
                new_address.user = request.user
                new_address.save()

        if is_valid:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_amount=pricing["grand_total"],
                    discount_applied=pricing["discount"],
                    tax_amount=pricing["tax"],
                    shipping_charge=pricing["shipping"],
                    coupon_code=pricing["coupon_code"],
                    shipping_address=shipping_address_str,
                )

                order_items = []
                for item in items:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                    order_items.append(order_item)
                    item.product.stock -= item.quantity
                    item.product.save(update_fields=["stock"])

                if pricing["coupon"]:
                    Coupon.objects.filter(pk=pricing["coupon"].pk).update(
                        times_used=F("times_used") + 1
                    )

                items.delete()
                request.session.pop(COUPON_SESSION_KEY, None)

            email_to = request.user.email or "customer@example.com"
            subject = f"Order Confirmation #{order.id}"
            message_body = [
                f"Thank you for your order! Your order ID is #{order.id}.",
                "",
                "Items Ordered:",
            ]
            for item in order_items:
                product_name = item.product.name if item.product else "Product"
                message_body.append(
                    f"- {product_name} (x{item.quantity}) - $ {item.price:.2f}"
                )
            message_body.extend(
                [
                    "",
                    f"Subtotal: $ {pricing['subtotal']:.2f}",
                    f"Discount: -$ {pricing['discount']:.2f}",
                    f"Tax: $ {pricing['tax']:.2f}",
                    f"Shipping: $ {pricing['shipping']:.2f}",
                    f"Total: $ {order.total_amount:.2f}",
                    "",
                    "Shipping Address:",
                    order.shipping_address,
                ]
            )
            send_mail(subject, "\n".join(message_body), None, [email_to])


            return render(request, "shop/order_success.html", {"order": order})
    else:
        address_form = AddressForm(prefix="new")
        shipping_form = ShippingAddressForm(user=request.user, prefix="shipping", initial={"shipping_address_id": default_address})

    return render(
        request,
        "shop/checkout.html",
        {
            "address_form": address_form,
            "shipping_form": shipping_form,
            "items": items,
            "pricing": pricing,
        },
    )


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__product"),
        pk=order_id,
        user=request.user,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=f"Invoice #{order.id}",
    )
    styles = getSampleStyleSheet()
    elements = []

    customer_name = order.user.get_full_name() or order.user.username
    order_subtotal = sum((item.price * item.quantity for item in order.items.all()), Decimal("0.00"))
    coupon_label = order.coupon_code or "None"

    elements.append(Paragraph("Ecommerce Store", styles["Title"]))
    elements.append(Paragraph("Computer Hardware Invoice", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Invoice #{order.id}", styles["Heading2"]))
    elements.append(
        Paragraph(
            f"Order Date: {order.created_at.strftime('%B %d, %Y %I:%M %p')}",
            styles["Normal"],
        )
    )
    elements.append(Paragraph(f"Status: {order.get_status_display()}", styles["Normal"]))
    elements.append(Paragraph(f"Coupon Code: {coupon_label}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    customer_table = Table(
        [
            ["Customer", customer_name],
            ["Username", order.user.username],
            ["Shipping Address", order.shipping_address],
        ],
        colWidths=[1.45 * inch, 5.3 * inch],
    )
    customer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1d4ed8")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbeafe")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(customer_table)
    elements.append(Spacer(1, 18))

    table_data = [["Product", "Qty", "Unit Price", "Line Total"]]
    for item in order.items.all():
        item_subtotal = item.price * item.quantity
        table_data.append([
            item.product.name if item.product else "Product unavailable",
            str(item.quantity),
            f"$ {item.price:.2f}",
            f"$ {item_subtotal:.2f}",
        ])

    table_data.extend([
        ["", "", "Subtotal", f"$ {order_subtotal:.2f}"],
        ["", "", f"Discount ({coupon_label})", f"-$ {order.discount_applied:.2f}"],
        ["", "", "Tax", f"$ {order.tax_amount:.2f}"],
        ["", "", "Shipping", f"$ {order.shipping_charge:.2f}"],
        ["", "", "Grand Total", f"$ {order.total_amount:.2f}"],
    ])

    table = Table(table_data, colWidths=[3.2 * inch, 0.7 * inch, 1.35 * inch, 1.35 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (2, -1), (-1, -1), colors.HexColor("#eff6ff")),
        ("SPAN", (0, -5), (1, -5)),
        ("SPAN", (0, -4), (1, -4)),
        ("SPAN", (0, -3), (1, -3)),
        ("SPAN", (0, -2), (1, -2)),
        ("SPAN", (0, -1), (1, -1)),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 18))
    elements.append(Paragraph("Thank you for shopping with Ecommerce Store.", styles["Italic"]))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{order.id}.pdf"'
    response["Content-Length"] = str(len(pdf))
    response["X-Content-Type-Options"] = "nosniff"
    return response

@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .select_related("user")
        .order_by("-created_at")
        .prefetch_related("items__product")
    )
    return render(request, "shop/order_history.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__product"),
        pk=pk,
        user=request.user,
    )

    statuses = Order.STATUS_CHOICES
    current_status_index = -1
    for i, (key, value) in enumerate(statuses):
        if key == order.status:
            current_status_index = i
            break

    subtotal = order.total_amount - order.tax_amount - order.shipping_charge + order.discount_applied

    return render(
        request,
        "shop/order_detail.html",
        {
            "order": order,
            "statuses": statuses,
            "current_status_index": current_status_index,
            "subtotal": subtotal,
        },
    )


@login_required
def view_wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "shop/wishlist.html", {"items": items})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user, product=product
    )
    in_wishlist = True
    if not created:
        wishlist_item.delete()
        in_wishlist = False

    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse(
        {
            "success": True,
            "in_wishlist": in_wishlist,
            "wishlist_count": wishlist_count,
        }
    )
