from django.apps import AppConfig
from django.db.models.signals import post_migrate
from .celery import app as celery_app


class CantusdataConfig(AppConfig):
    name = "cantusdata"
    verbose_name = "Cantus Ultimus"

    def ready(self):
        # Enable the app's signals
        import cantusdata.signals

        post_migrate.connect(
            cantusdata.signals.solr_synchronizer.db_refresh, sender=self
        )

        # Metrics: Celery task signals connect on import.
        from django.contrib.auth.signals import user_logged_in, user_login_failed
        from django.db.backends.signals import connection_created
        import cantusdata.metrics.celery_signals  # pylint: disable=unused-import
        from cantusdata.metrics import events, search_log
        from cantusdata.metrics.build import publish_build_info
        from cantusdata.metrics.db import install_query_wrapper

        connection_created.connect(install_query_wrapper)
        user_logged_in.connect(events.login_succeeded)
        user_login_failed.connect(events.login_failed)
        search_log.configure()
        publish_build_info()
