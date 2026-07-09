"""
ASGI config for Ecommerce_Store project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_core.settings")

application = get_asgi_application()
