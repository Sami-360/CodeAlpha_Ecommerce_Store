from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CartItem, Product


class StoreViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
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

    def test_product_detail_view_returns_200_for_valid_product(self):
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_checkout_redirects_to_login_when_not_authenticated(self):
        response = self.client.get(reverse("checkout"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_logout_get_works(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))

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
