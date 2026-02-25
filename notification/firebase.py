import json

import firebase_admin
from django.conf import settings
from firebase_admin import credentials


def get_firebase_app():
    # Prevent double-init if Django auto-reloads or multiple imports happen
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
        firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()
