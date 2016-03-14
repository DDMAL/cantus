from django.apps import AppConfig
from django.db.models.signals import post_migrate


default_app_config = 'cantusdata.CantusdataConfig'


class CantusdataConfig (AppConfig):
    name = 'cantusdata'
    verbose_name = 'Cantus Ultimus'

    def ready(self):
        # Enable the app's signals
        import cantusdata.signals

        post_migrate.connect(cantusdata.signals.solr_synchronizer.db_flushed, sender=self)
