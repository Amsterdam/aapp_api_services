from django.apps import AppConfig
from django.conf import settings


class CityPassConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "city_pass"
    verbose_name = "Stadspas"

    def ready(self):
        from core import authentication

        if settings.MOCK_ENTRA_AUTH:
            authentication.EntraCookieTokenAuthentication = (
                authentication.MockEntraCookieTokenAuthentication
            )
