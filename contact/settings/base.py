from core.settings.base import *  # isort:skip

SERVICE_NAME = "contact"
INSTALLED_APPS += [
    "contact.apps.ContactConfig",
]

ROOT_URLCONF = "contact.urls"

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "core.authentication.APIKeyAuthentication",
]

SPECTACULAR_SETTINGS["TITLE"] = "Contact API"

CSV_DIR = os.getenv("CSV_DIR")

WAITING_TIME_API = "https://wachttijdenamsterdam.nl/data/"

CITY_OFFICE_LOOKUP_TABLE = {
    5: "e9871a7716da02a4c20cfb06f9547005",  # Centrum
    6: "5d9637689a8b902fa1a13acdf0006d26",  # Nieuw-West
    7: "081d6a38f46686905693fcd6087039f5",  # Noord
    8: "29e3b63d09d1f0c9a9c7238064c70790",  # Oost
    9: "b4b178107cbc0c609d8d190bbdbdfb08",  # West
    10: "b887a4d081821c4245c02f07e2de3290",  # Zuid
    11: "d338d28f8e6132ea2cfcf3e61785454c",  # Zuidoost
}

STATIC_URL = "/contact/static/"
