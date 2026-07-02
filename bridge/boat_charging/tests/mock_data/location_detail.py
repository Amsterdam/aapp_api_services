MOCK_RESPONSE = {
    "id": "2c0ccabc15d040e39136b7abc125f13e",
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
    "chargingStationsIds": ["VCPS-7BMY2", "VCPS-MX1VV", "VCPS-IFZTY"],
    "chargingStations": [
        {
            "id": "VCPS-7BMY2",
            "status": "OFFLINE",
            "locationId": "2c0ccabc15d040e39136b7abc125f13e",
            "evses": [
                {
                    "id": 17,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "FAULTED",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 1,
                            "voltage": 1,
                            "maxElectricPower": 22000,
                            "status": "FAULTED",
                        }
                    ],
                }
            ],
        },
        {
            "id": "VCPS-IFZTY",
            "status": "OFFLINE",
            "locationId": "2c0ccabc15d040e39136b7abc125f13e",
            "evses": [
                {
                    "id": 30,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "OCCUPIED",
                    "substatus": "PREPARING",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 1,
                            "voltage": 1,
                            "status": "OCCUPIED",
                        }
                    ],
                }
            ],
        },
        {
            "id": "VCPS-MX1VV",
            "status": "OFFLINE",
            "locationId": "2c0ccabc15d040e39136b7abc125f13e",
            "evses": [
                {
                    "id": 2,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "UNKNOWN",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 32,
                            "voltage": 400,
                            "status": "UNKNOWN",
                        }
                    ],
                }
            ],
        },
    ],
    "availableSockets": 0,
    "totalSockets": 3,
}
