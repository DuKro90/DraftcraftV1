from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Utilities & Constants'

    def ready(self):
        """Initialize core module."""
        # Import signals or other initialization code here
        pass
