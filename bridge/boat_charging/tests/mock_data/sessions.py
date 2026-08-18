SESSION_WITHOUT_CPMS_STATUS_ID = "dda5b3d6-d541-4022-8008-fca5d2e404eb"
ACTIVE_SESSION_IDS = [
    "ad976dab-73db-4f67-b5f5-77542bf3e088",
    "82621518-fc55-4213-8833-39404382f121",
]
COMPLETED_SESSION_ID = "c7d62a24-53fd-4bc4-864e-33545c2c2ccb"


MOCK_RESPONSE = [
    {
        "session": {
            "uniqueId": SESSION_WITHOUT_CPMS_STATUS_ID,
            "stationId": "string",
            "socketNumber": "0",
            "status": 1,
            "finalAmount": 0.0,
            "desiredAmount": 45.0,
            "createdAt": "2026-06-29T12:09:21.5983604",
            "userEmail": "test@amsterdam.nl",
        }
    },
    {
        "session": {
            "uniqueId": ACTIVE_SESSION_IDS[0],
            "stationId": "VCPS-IFZTY",
            "socketNumber": "1",
            "status": 2,
            "finalAmount": 0.0,
            "desiredAmount": 45.0,
            "createdAt": "2026-06-29T10:30:04.1035904",
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
            "userEmail": "test@amsterdam.nl",
            "lastCommandError": "The charge point rejected the start command. Check that the cable is plugged in and try again.",
        },
        "cpmsSession": {
            "startDateTime": "2026-06-29T10:35:04.1035904",
            "status": "ACTIVE",
            "kwh": 12.5,
            "totalCost": {"exclVat": 4.2},
        },
        "location": {
            "id": "2c0ccfb795d040e39136b7dd1d25f13e",
            "name": "AmsterdamBoatTest1",
            "address": "Isolatorweg 178",
            "city": "Amsterdam",
            "postalCode": "1234 AM",
            "coordinates": {"latitude": "52.327549", "longitude": "4.972519"},
            "openingTimes": {
                "twentyfourseven": False,
                "regularHours": [
                    {"weekday": 1, "periodBegin": "17:41", "periodEnd": "19:41"},
                    {"weekday": 6, "periodBegin": "13:41", "periodEnd": "17:41"},
                ],
            },
            "availableSockets": 0,
            "totalSockets": 0,
        },
    },
    {
        "session": {
            "uniqueId": ACTIVE_SESSION_IDS[1],
            "stationId": "VCPS-7BMY2",
            "socketNumber": "17",
            "status": 2,
            "finalAmount": 0.0,
            "desiredAmount": 45.0,
            "createdAt": "2026-06-19T11:49:38.6577696",
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
            "lastCommandError": "The charge point rejected the start command. Check that the cable is plugged in and try again.",
        },
        "cpmsSession": {
            "startDateTime": "2026-06-19T11:50:38.6577696",
            "status": "ACTIVE",
            "kwh": 8.75,
            "totalCost": {"exclVat": 2.9},
        },
        "location": {
            "id": "2c0ccfb795d040e39136b7dd1d25f13e",
            "name": "AmsterdamBoatTest1",
            "address": "Isolatorweg 178",
            "city": "Amsterdam",
            "postalCode": "1234 AM",
            "coordinates": {"latitude": "52.327549", "longitude": "4.972519"},
            "openingTimes": {
                "twentyfourseven": False,
                "regularHours": [
                    {"weekday": 1, "periodBegin": "17:41", "periodEnd": "19:41"},
                    {"weekday": 6, "periodBegin": "13:41", "periodEnd": "17:41"},
                ],
            },
            "availableSockets": 0,
            "totalSockets": 0,
        },
    },
    {
        "session": {
            "uniqueId": COMPLETED_SESSION_ID,
            "stationId": "VCPS-9XQ21",
            "socketNumber": "4",
            "status": 4,
            "finalAmount": 12.0,
            "desiredAmount": 45.0,
            "createdAt": "2026-06-18T08:11:12.1010101",
        },
        "cpmsSession": {
            "startDateTime": "2026-06-18T08:15:12.1010101",
            "endDateTime": "2026-06-18T09:00:12.1010101",
            "status": "COMPLETED",
            "kwh": 14.0,
            "totalCost": {"exclVat": 5.6},
        },
    },
    {
        "session": {
            "uniqueId": "75bd25a9-ad17-473f-a19b-d2c65d608e0d",
            "stationId": "VCPS-IFZTY",
            "socketNumber": "1",
            "status": 5,
            "finalAmount": 0.0,
            "desiredAmount": 45.0,
            "createdAt": "2026-07-16T09:15:26.3524708",
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
            "userEmail": "j.beekman@amsterdam.nl",
            "stopReason": "cancelled",
        },
        "location": {
            "id": "2c0ccfb795d040e39136b7dd1d25f13e",
            "name": "AmsterdamBoatTest1",
            "address": "Isolatorweg 178",
            "city": "Amsterdam",
            "postalCode": "1234 AM",
            "coordinates": {"latitude": "52.327549", "longitude": "4.972519"},
            "openingTimes": {
                "twentyfourseven": False,
                "regularHours": [
                    {"weekday": 1, "periodBegin": "17:41", "periodEnd": "19:41"},
                    {"weekday": 6, "periodBegin": "13:41", "periodEnd": "17:41"},
                ],
            },
            "tariffId": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
            "availableSockets": 0,
            "totalSockets": 0,
        },
    },
    {
        "session": {
            "uniqueId": "75bd25a9-ad17-473f-a19b-d2c65d608e0d",
            "stationId": "VCPS-IFZTY",
            "socketNumber": "1",
            "status": 5,
            "finalAmount": 0.0,
            "desiredAmount": 45.0,
            "createdAt": "2026-07-16T09:15:26.3524708",
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
            "userEmail": "test-cancelled@amsterdam.nl",
            "stopReason": "cancelled",
        },
        "location": {
            "id": "2c0ccfb795d040e39136b7dd1d25f13e",
            "name": "AmsterdamBoatTest1",
            "address": "Isolatorweg 178",
            "city": "Amsterdam",
            "postalCode": "1234 AM",
            "coordinates": {"latitude": "52.327549", "longitude": "4.972519"},
            "openingTimes": {
                "twentyfourseven": False,
                "regularHours": [
                    {"weekday": 1, "periodBegin": "17:41", "periodEnd": "19:41"},
                    {"weekday": 6, "periodBegin": "13:41", "periodEnd": "17:41"},
                ],
            },
            "tariffId": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
            "availableSockets": 0,
            "totalSockets": 0,
        },
    },
]
