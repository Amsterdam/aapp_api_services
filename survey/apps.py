from django.apps import AppConfig
from django.conf import settings


class SurveyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "survey"
    verbose_name = "Vragenlijsten"

    def ready(self):
        from core import authentication

        if settings.MOCK_ENTRA_AUTH:
            authentication.EntraCookieTokenAuthentication = (
                authentication.MockEntraCookieTokenAuthentication
            )
