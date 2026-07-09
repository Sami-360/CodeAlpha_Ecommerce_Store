# Ecommerce Store

A polished Django ecommerce application for a computer hardware store. The app supports catalog browsing, product detail pages, wishlist, cart, checkout, coupons, profiles, order tracking, PDF invoices, static pages, and store/admin analytics.

## Screenshots

Add screenshots after deployment or local capture:

- `docs/screenshots/homepage.png`
- `docs/screenshots/product-detail.png`
- `docs/screenshots/cart-checkout.png`
- `docs/screenshots/admin-dashboard.png`

## Features

- Product catalog with search, category filtering, sorting, and pagination
- Product detail pages with gallery support, reviews, ratings, related products, SEO metadata, and Open Graph tags
- Graceful product image fallback for missing uploaded images
- User registration with first name, last name, unique email, username, and password
- Login/logout messaging and session-based login rate limiting
- Wishlist/favorites with AJAX toggle buttons
- Shopping cart with AJAX add-to-cart and quantity updates
- Coupon validation, tax, shipping, and full checkout price breakdown
- Checkout with saved address selection and optional new address saving
- Order history, order detail status timeline, and downloadable PDF invoices
- Console email backend for local order confirmation testing
- User profile and address book
- Contact form and newsletter subscriber capture
- About, contact, privacy policy, terms of service, 404, and 500 pages
- Staff-only analytics dashboard with revenue, order status counts, low stock products, recent orders, and Chart.js top-seller chart
- Custom Django admin styling with light/dark theme token support
- Demo catalog seeding command for tech products and coupons
- Image upload size validation
- WhiteNoise static-file support for production hosting

## Tech Stack

- Python 3.12
- Django 6
- SQLite for local development
- Bootstrap 5 and Bootstrap Icons
- Chart.js
- Pillow
- ReportLab
- python-dotenv
- WhiteNoise
- Gunicorn

## Project Structure

```text
Ecommerce_Store/
|-- .env.example
|-- .gitignore
|-- Procfile
|-- README.md
|-- manage.py
|-- requirements.txt
|-- runtime.txt
|-- docs/
|   `-- API_endpoints.md
|-- ecommerce_core/
|   |-- __init__.py
|   |-- asgi.py
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|-- shop/
|   |-- __init__.py
|   |-- admin.py
|   |-- admin_views.py
|   |-- apps.py
|   |-- context_processors.py
|   |-- forms.py
|   |-- models.py
|   |-- signals.py
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   |-- management/
|   |   |-- __init__.py
|   |   `-- commands/
|   |       |-- __init__.py
|   |       `-- seed_products.py
|   |-- migrations/
|   |   |-- 0001_initial.py
|   |   |-- 0002_productimage_review.py
|   |   |-- 0003_coupon_order_coupon_code_order_discount_applied_and_more.py
|   |   |-- 0004_address_userprofile.py
|   |   |-- 0005_contactmessage_newslettersubscriber.py
|   |   |-- 0006_alter_product_image_alter_productimage_image.py
|   |   |-- 0007_alter_address_options.py
|   |   |-- 0008_product_image_url.py
|   |   `-- __init__.py
|   |-- static/
|   |   `-- shop/
|   |       |-- css/
|   |       |   |-- admin.css
|   |       |   |-- base.css
|   |       |   `-- wishlist.css
|   |       `-- js/
|   |           |-- cart.js
|   |           `-- wishlist.js
|   `-- templates/
|       |-- base.html
|       |-- registration/
|       |   |-- login.html
|       |   `-- register.html
|       `-- shop/
|           |-- about.html
|           |-- admin_dashboard.html
|           |-- cart.html
|           |-- checkout.html
|           |-- contact.html
|           |-- order_detail.html
|           |-- order_history.html
|           |-- order_success.html
|           |-- privacy_policy.html
|           |-- product_detail.html
|           |-- product_list.html
|           |-- profile.html
|           |-- terms_of_service.html
|           `-- wishlist.html
`-- templates/
    |-- 404.html
    |-- 500.html
    `-- admin/
        |-- base_site.html
        `-- index.html
```

Local runtime folders such as `.venv/`, `db.sqlite3`, `.env`, `media/`, `staticfiles/`, and Python cache folders are intentionally ignored by Git.

## Local Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a local environment file:

```powershell
Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Put the generated key in `.env`:

```env
SECRET_KEY=replace-with-generated-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=
SECURE_SSL_REDIRECT=False
```

4. Apply migrations:

```powershell
python manage.py migrate
```

5. Create an admin account:

```powershell
python manage.py createsuperuser
```

6. Seed the demo catalog and coupons:

```powershell
python manage.py seed_products
```

Sample coupon codes:

```text
WELCOME10
EID20
FREESHIP15
RAMADAN25
```

7. Start the development server:

```Windows PowerShell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Admin:

```text
http://127.0.0.1:8000/admin/
```

## Useful Commands

```powershell
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py seed_products
python manage.py collectstatic
```

## Deployment

This project includes a `Procfile`, `runtime.txt`, Gunicorn, and WhiteNoise for platforms such as Render or Railway.

Set these production environment variables on the hosting platform:

```env
SECRET_KEY=<strong-production-secret>
DEBUG=False
ALLOWED_HOSTS=<your-domain>,<your-service-hostname>
CSRF_TRUSTED_ORIGINS=https://<your-domain>
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Run migrations and collect static files during deployment:

```powershell
python manage.py migrate
python manage.py collectstatic --noinput
```

## Notes

- Uploaded files in `media/` are local runtime data and are ignored by Git.
- SQLite is suitable for local development. Use a managed production database for real deployments.
- The email backend is configured for console output in development.
