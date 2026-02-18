from core.settings.base import *  # isort:skip

SERVICE_NAME = "survey"
INSTALLED_APPS += [
    "survey.apps.SurveyConfig",
    "notification.apps.NotificationsConfig",
]
MIDDLEWARE += [
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

X_FRAME_OPTIONS = "SAMEORIGIN"
LANGUAGE_CODE = "nl-NL"

ROOT_URLCONF = "survey.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Vragenlijsten API"


TIME_INPUT_FORMATS = ["%H:%M"]

MOCK_ENTRA_AUTH = False
ADMIN_ROLES += ["survey-delegated", "survey-publisher"]
