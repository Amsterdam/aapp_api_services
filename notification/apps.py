import json

import firebase_admin
from django.apps import AppConfig
from django.conf import settings
from firebase_admin import credentials


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification"

    def ready(self):
        from notification.utils.patch_utils import setup_local_development_patches

        self.get_firebase_app()

        if settings.MOCK_FIREBASE:
            setup_local_development_patches()

    def get_firebase_app(self):
        # Prevent double-init if Django auto-reloads or multiple imports happen
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
            firebase_admin.initialize_app(cred)
        return firebase_admin.get_app()
