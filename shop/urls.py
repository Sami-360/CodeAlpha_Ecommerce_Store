from django.urls import path

from .admin_views import admin_dashboard
from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms_of_service, name="terms_of_service"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("product/<int:pk>/review/", views.add_review, name="add_review"),
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/coupon/", views.apply_coupon, name="apply_coupon"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_quantity, name="update_cart_quantity"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("orders/", views.order_history, name="order_history"),
    path("order/<int:pk>/", views.order_detail, name="order_detail"),
    path("order/<int:order_id>/invoice/", views.download_invoice, name="download_invoice"),
    path("profile/", views.profile, name="profile"),
    path("profile/address/delete/<int:pk>/", views.delete_address, name="delete_address"),
    path(
        "profile/address/default/<int:pk>/",
        views.set_default_address,
        name="set_default_address",
    ),
    path("register/", views.register, name="register"),
    path("wishlist/", views.view_wishlist, name="view_wishlist"),
    path(
        "wishlist/toggle/<int:product_id>/",
        views.toggle_wishlist,
        name="toggle_wishlist",
    ),
]
