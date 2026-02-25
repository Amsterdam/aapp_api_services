import json

import firebase_admin
from django.conf import settings
from firebase_admin import credentials
import threading

_firebase_app_lock = threading.Lock()


def get_firebase_app():
    # Use public API and guard initialization with a lock to avoid races.
    try:
        return firebase_admin.get_app()
    except ValueError:
        # App not initialized yet; initialize it in a thread-safe manner.
        with _firebase_app_lock:
            try:
                # Another thread may have initialized the app while we were waiting.
                return firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
                firebase_admin.initialize_app(cred)
                return firebase_admin.get_app()
