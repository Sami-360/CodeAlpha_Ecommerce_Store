# Ecommerce_Store

A Django-based computer hardware e-commerce store with product browsing, authentication, wishlist, cart management, coupons, checkout, order history, reviews, and an admin panel for managing store data.

## Tech Stack

- Python
- Django
- SQLite
- Bootstrap 5
- Bootstrap Icons
- Pillow
- reportlab
- python-dotenv

## Features

- Product listing with category filtering and sorting
- Product search and pagination
- Product detail pages with gallery images and Open Graph metadata
- Customer reviews, star ratings, and related products
- User registration, login, and logout
- Wishlist management with AJAX toggles
- Shopping cart with AJAX add-to-cart and quantity update support
- Coupon codes, tax calculation, shipping fees, and checkout pricing breakdown
- Checkout with address selection and order creation
- Order history and PDF invoice generation
- Contact form for customer messages
- Newsletter subscription via AJAX
- Custom 404 and 500 error pages
- Admin analytics dashboard and Django admin management
- Session-based login rate limiting for security
- Product list caching and query optimizations for performance
- Image upload validation to enforce a 5MB file size limit
- Catalog seeding command for laptops, processors, graphics cards, memory, storage, and PC tools

## Folder Structure

```text
Ecommerce_Store/
|-- .env.example
|-- .gitignore
|-- docs/
|   `-- API_endpoints.md
|-- ecommerce_core/
|   |-- __init__.py
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|-- media/
|   `-- products/
|       `-- gallery/
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
|   |   `-- __init__.py
|   |-- static/
|   |   `-- shop/
|   |       |-- css/
|   |       |   |-- base.css
|   |       |   `-- wishlist.css
|   |       `-- js/
|   |           |-- cart.js
|   |           `-- wishlist.js
|   |-- templates/
|   |   |-- base.html
|   |   |-- registration/
|   |   |   |-- login.html
|   |   |   `-- register.html
|   |   |-- shop/
|   |   |   |-- about.html
|   |   |   |-- admin_dashboard.html
|   |   |   |-- cart.html
|   |   |   |-- checkout.html
|   |   |   |-- contact.html
|   |   |   |-- order_detail.html
|   |   |   |-- order_history.html
|   |   |   |-- order_success.html
|   |   |   |-- privacy_policy.html
|   |   |   |-- product_detail.html
|   |   |   |-- product_list.html
|   |   |   |-- profile.html
|   |   |   |-- terms_of_service.html
|   |   |   `-- wishlist.html
|-- templates/
|   |-- 404.html
|   `-- 500.html
|-- manage.py
|-- requirements.txt
`-- README.md
```

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
```

4. Run migrations:

```powershell
python manage.py migrate
```

5. Create an admin user:

```powershell
python manage.py createsuperuser
```

6. Seed catalog products and coupons:

```powershell
python manage.py seed_products
```

The seeder clears old product media and assigns external tech photo URLs for laptops, CPUs, GPUs, memory, storage, and PC tools. Uploaded local images still work through Django admin when needed.

Sample coupon codes:

```text
WELCOME10
EID20
FREESHIP15
```

7. Start the development server:

```powershell
python manage.py runserver
```

8. Open the app:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## Tests

Run the test suite:

```powershell
python manage.py test
```
