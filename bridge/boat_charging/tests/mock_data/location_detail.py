MOCK_RESPONSE = {
    "id": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
    "name": "AmsterdamBoatTest3",
    "address": "Funenkade 7",
    "city": "Amsterdam",
    "postalCode": "1093 SJ",
    "coordinates": {"latitude": "52.366474", "longitude": "4.926436"},
    "openingTimes": {
        "twentyfourseven": False,
        "regularHours": [
            {"weekday": 1, "periodBegin": "04:15", "periodEnd": "12:15"},
            {"weekday": 3, "periodBegin": "09:15", "periodEnd": "16:15"},
            {"weekday": 4, "periodBegin": "09:15", "periodEnd": "15:15"},
            {"weekday": 2, "periodBegin": "10:15", "periodEnd": "12:15"},
        ],
    },
    "chargingStationsIds": ["VCPS-RIK", "VCPS-MULTI", "VCPS-7BMY3"],
    "tariffId": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
    "tariff": {
        "id": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
        "energyPricePerKwh": 0.23,
        "chargingTimePricePerHour": 0.45,
        "parkingTimePricePerHour": 0.12,
        "flatFeePrice": 1.0,
        "standardFine": 0.0,
        "standardFineAfterHours": 24.0,
    },
    "chargingStations": [
        {
            "id": "VCPS-MULTI",
            "status": "AVAILABLE",
            "locationId": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
            "evses": [
                {
                    "id": 57,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "OCCUPIED",
                    "substatus": "FINISHING",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 17,
                            "voltage": 230,
                            "maxElectricPower": 11.7,
                            "status": "OCCUPIED",
                        }
                    ],
                },
                {
                    "id": 56,
                    "ocppEvseId": 2,
                    "evseId": "2",
                    "status": "AVAILABLE",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 17,
                            "voltage": 230,
                            "maxElectricPower": 11.7,
                            "status": "AVAILABLE",
                        }
                    ],
                },
            ],
        },
        {
            "id": "VCPS-RIK",
            "status": "OFFLINE",
            "locationId": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
            "evses": [
                {
                    "id": 51,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "AVAILABLE",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 1,
                            "voltage": 1,
                            "status": "AVAILABLE",
                        }
                    ],
                }
            ],
        },
    ],
    "availableSockets": 1,
    "totalSockets": 3,
}

MOCK_RESPONSE_OFFLINE_CHARGING_STATION = {
    "id": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
    "name": "AmsterdamBoatTest3",
    "address": "Funenkade 7",
    "city": "Amsterdam",
    "postalCode": "1093 SJ",
    "coordinates": {"latitude": "52.366474", "longitude": "4.926436"},
    "openingTimes": {
        "twentyfourseven": False,
        "regularHours": [
            {"weekday": 1, "periodBegin": "04:15", "periodEnd": "12:15"},
            {"weekday": 3, "periodBegin": "09:15", "periodEnd": "16:15"},
            {"weekday": 4, "periodBegin": "09:15", "periodEnd": "15:15"},
            {"weekday": 2, "periodBegin": "10:15", "periodEnd": "12:15"},
        ],
    },
    "chargingStationsIds": ["VCPS-RIK", "VCPS-7BMY3"],
    "tariffId": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
    "tariff": {
        "id": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
        "energyPricePerKwh": 0.23,
        "chargingTimePricePerHour": 0.45,
        "parkingTimePricePerHour": 0.12,
        "flatFeePrice": 1.0,
        "standardFine": 0.0,
        "standardFineAfterHours": 24.0,
    },
    "chargingStations": [
        {
            "id": "VCPS-RIK",
            "status": "OFFLINE",
            "locationId": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
            "evses": [
                {
                    "id": 51,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "AVAILABLE",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 1,
                            "voltage": 1,
                            "status": "AVAILABLE",
                        }
                    ],
                }
            ],
        }
    ],
    "availableSockets": 0,
    "totalSockets": 1,
}
