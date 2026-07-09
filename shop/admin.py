from django.contrib import admin

from .models import (
    Address,
    ContactMessage,
    Coupon,
    NewsletterSubscriber,
    Order,
    OrderItem,
    Product,
    ProductImage,
    Review,
    UserProfile,
)

admin.site.site_header = "Ecommerce Store Admin"
admin.site.site_title = "Ecommerce Store Admin"
admin.site.index_title = "Store Management"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "category", "created_at")
    search_fields = ("name", "description", "image_url")
    list_filter = ("category",)
    inlines = (ProductImageInline,)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_amount",
        "discount_applied",
        "tax_amount",
        "shipping_charge",
        "coupon_code",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    inlines = (OrderItemInline,)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "city", "is_default")
    list_filter = ("is_default", "city")
    search_fields = ("user__username", "label", "city")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "created_at")
    search_fields = ("user__username", "phone_number")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at")
    search_fields = ("email",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__username", "comment")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "active", "times_used", "valid_until")
    list_filter = ("active", "valid_until")
    search_fields = ("code",)
