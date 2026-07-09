"""
WSGI config for Ecommerce_Store project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_core.settings")

application = get_wsgi_application()
