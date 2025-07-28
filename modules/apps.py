"""Django app config"""

from django.apps import AppConfig
from django.conf import settings
from django.db import models


class ModulesConfig(AppConfig):
    """Amsterdam App Api Configuration"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules"

    def ready(self):
        from core import authentication

        _orig = models.URLField.formfield

        def _https_formfield(self, **kwargs):
            kwargs.setdefault("assume_scheme", "https")
            return _orig(self, **kwargs)

        models.URLField.formfield = _https_formfield
        if settings.MOCK_ENTRA_AUTH:
            authentication.EntraCookieTokenAuthentication = (
                authentication.MockEntraCookieTokenAuthentication
            )
