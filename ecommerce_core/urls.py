from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from shop import views as shop_views
from shop.admin_views import admin_dashboard

handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"

urlpatterns = [
    # Register the analytics dashboard route before the admin site so /admin/dashboard/ is handled here
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/", admin.site.urls),
    path("accounts/login/", shop_views.login_view, name="login"),
    path("accounts/logout/", shop_views.logout_view, name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("shop.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
