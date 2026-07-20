OPERATION_STATE_CHOICES = ["OPERATIVE", "INOPERATIVE", "OFFLINE", "UNKNOWN", "OCCUPIED"]

OPERATION_STATE_MAPPING = {
    "OPERATIVE": "OPERATIVE",
    "INOPERATIVE": "INOPERATIVE",
    "OFFLINE": "OFFLINE",
    "UNKNOWN": "UNKNOWN",
    "OCCUPIED": "OCCUPIED",
    "FAULTED": "INOPERATIVE",
    "AVAILABLE": "OPERATIVE",
    "CHARGING": "OCCUPIED",
    "RESERVED": "OCCUPIED",
}

OCCUPIED_SUBSTATUS_CHOICES = [
    "PREPARING",  # important: cable is plugged in, without that session can not be started
    "CHARGING",
    "SUSPENDED_EV",  # boat refusing to charge (e.g. battery full)
    "SUSPENDED_EVSE",  # EVSE (charging station) refusing to charge
    "FINISHING",
]
