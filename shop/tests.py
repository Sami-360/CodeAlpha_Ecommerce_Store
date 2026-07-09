from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Address, CartItem, Order, OrderItem, Product, Wishlist


class StoreViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPass12345",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="StrongPass12345",
        )
        self.product = Product.objects.create(
            name="Test Product",
            description="A product used for tests.",
            price=Decimal("19.99"),
            stock=5,
            category="Test",
        )

    def test_cart_item_total_price_calculates_correctly(self):
        item = CartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=3,
        )

        self.assertEqual(item.get_total_item_price(), Decimal("59.97"))

    def test_product_list_search_filters_products(self):
        Product.objects.create(
            name="Hidden Monitor",
            description="Another item.",
            price=Decimal("99.99"),
            stock=5,
            category="Displays",
        )

        response = self.client.get(reverse("product_list"), {"q": "Test Product"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertNotContains(response, "Hidden Monitor")

    def test_product_detail_view_returns_200_for_valid_product(self):
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_checkout_redirects_to_login_when_not_authenticated(self):
        response = self.client.get(reverse("checkout"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_post_redirects_to_product_list(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("product_list"))

    def test_register_logs_in_new_user(self):
        username = "newuser"
        password = "StrongPass123"
        response = self.client.post(
            reverse("register"),
            {
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "username": username,
                "password1": password,
                "password2": password,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("product_list"))
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            User.objects.get(username=username).pk,
        )

    def test_order_detail_is_limited_to_owner(self):
        order = Order.objects.create(
            user=self.other_user,
            total_amount=Decimal("19.99"),
            shipping_address="Other customer address",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("order_detail", args=[order.pk]))

        self.assertEqual(response.status_code, 404)

    def test_invoice_download_returns_pdf_for_owner(self):
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("19.99"),
            shipping_address="House 1, Test Street",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("download_invoice", args=[order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment;", response["Content-Disposition"])

    def test_invoice_download_is_limited_to_owner(self):
        order = Order.objects.create(
            user=self.other_user,
            total_amount=Decimal("19.99"),
            shipping_address="Other customer address",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("download_invoice", args=[order.pk]))

        self.assertEqual(response.status_code, 404)

    def test_wishlist_toggle_requires_post_and_login(self):
        get_response = self.client.get(reverse("toggle_wishlist", args=[self.product.pk]))
        self.assertEqual(get_response.status_code, 302)

        self.client.force_login(self.user)
        post_response = self.client.post(reverse("toggle_wishlist", args=[self.product.pk]))

        self.assertEqual(post_response.status_code, 200)
        self.assertTrue(
            Wishlist.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_address_delete_is_limited_to_owner(self):
        address = Address.objects.create(
            user=self.other_user,
            label="Home",
            full_address="Other address",
            city="Karachi",
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("delete_address", args=[address.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Address.objects.filter(pk=address.pk).exists())

    def test_admin_dashboard_requires_staff(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_allows_staff(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
