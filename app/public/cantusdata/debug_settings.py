"""
Overwrites some main settings that are used in development.
"""

from .settings import *

DEBUG = is_development

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: (
        False if request.headers.get("x-requested-with") == "XMLHttpRequest" else True
    ),
}
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INSTALLED_APPS.extend(["django_extensions", "debug_toolbar"])


SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
