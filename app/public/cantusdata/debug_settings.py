"""
Overwrites some main settings that are used in development.
"""

from .settings import *

DEBUG = is_development

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": {
        "debug_toolbar.panels.history.HistoryPanel",
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    },
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
