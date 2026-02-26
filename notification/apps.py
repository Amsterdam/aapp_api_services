from django.apps import AppConfig
from django.conf import settings

from notification.firebase import get_firebase_app


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification"

    def ready(self):
        from notification.utils.patch_utils import setup_local_development_patches

        if settings.MOCK_FIREBASE:
            setup_local_development_patches()
        elif settings.FIREBASE_CREDENTIALS:
            get_firebase_app()
