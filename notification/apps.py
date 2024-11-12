from django.apps import AppConfig
from django.conf import settings


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification"

    def ready(self):
        from notification.utils.patch_utils import setup_local_development_patches

        if settings.MOCK_FIREBASE:
            setup_local_development_patches()
