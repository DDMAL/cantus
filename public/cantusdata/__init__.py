from django.apps import AppConfig


default_app_config = 'cantusdata.CantusdataConfig'


class CantusdataConfig (AppConfig):
    name = 'cantusdata'
    verbose_name = 'Cantus Ultimus'

    def ready(self):
        # Enable the app's signals
        import cantusdata.signals
