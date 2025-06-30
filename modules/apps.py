"""Django app config"""

from django.apps import AppConfig
from django.conf import settings


class ModulesConfig(AppConfig):
    """Amsterdam App Api Configuration"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules"

    def ready(self):
        from core import authentication

        if settings.MOCK_ENTRA_AUTH:
            authentication.EntraCookieTokenAuthentication = (
                authentication.MockEntraCookieTokenAuthentication
            )
