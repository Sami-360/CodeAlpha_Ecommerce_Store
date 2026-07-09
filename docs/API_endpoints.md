check the image , plz correct the w# API Endpoints

| URL path | HTTP method | Purpose |
| --- | --- | --- |
| `/` | GET | Show the product list with optional `?category=` filtering. |
| `/product/<int:pk>/` | GET | Show details for a single product. |
| `/cart/` | GET | Show the logged-in user's cart. |
| `/cart/add/<int:product_id>/` | POST | Add a product to the logged-in user's cart and return JSON with the updated cart count. |
| `/cart/update/<int:item_id>/` | POST | Update a cart item quantity and return JSON with updated totals. |
| `/cart/remove/<int:item_id>/` | GET | Remove an item from the cart and redirect back to the cart page. |
| `/checkout/` | GET | Show checkout page with order summary and shipping address form. |
| `/checkout/` | POST | Create an order from cart items, deduct stock, clear cart, and show confirmation. |
| `/orders/` | GET | Show order history for the logged-in user. |
| `/register/` | GET | Show the user registration form. |
| `/register/` | POST | Create a new user, log them in, and redirect to product list. |
