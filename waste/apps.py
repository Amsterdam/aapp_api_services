from django.apps import AppConfig
from django.conf import settings


class WasteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "waste"
    verbose_name = "Afval en Grondstoffen"

    def ready(self):
        from core import authentication

        if settings.MOCK_ENTRA_AUTH:
            authentication.EntraCookieTokenAuthentication = (
                authentication.EntraCookieTokenAuthentication
            )
