from django.apps import AppConfig
from django.conf import settings


class ConstructionWorkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "construction_work"

    def ready(self):
        from construction_work import authentication

        if settings.MOCK_ENTRA_AUTH:
            authentication.EntraIDAuthentication = (
                authentication.MockEntraIDAuthentication
            )
