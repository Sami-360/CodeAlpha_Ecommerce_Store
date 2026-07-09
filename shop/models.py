from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


def validate_image_size(image):
    max_size = 5 * 1024 * 1024
    if image and image.size > max_size:
        raise ValidationError("Image file size must be 5MB or smaller.")


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True, validators=[validate_image_size])
    image_url = models.URLField(blank=True)
    stock = models.IntegerField(default=0)
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/gallery/", validators=[validate_image_size])
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} image"


class CartItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_item_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for {self.user.username}"


class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ("-added_at",)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField()
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=100)
    times_used = models.IntegerField(default=0)

    def __str__(self):
        return self.code


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} - {self.email}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-subscribed_at",)

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone_number = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} profile"


class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(max_length=50)
    full_address = models.TextField()
    city = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("-is_default", "label")
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.label} - {self.city}"


class Order(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_PROCESSING = "Processing"
    STATUS_COMPLETED = "Completed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted product"
        return f"{self.quantity} x {product_name}"


class Review(models.Model):
    RATING_CHOICES = [
        (1, "1 star"),
        (2, "2 stars"),
        (3, "3 stars"),
        (4, "4 stars"),
        (5, "5 stars"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.product.name} review by {self.user.username}"
