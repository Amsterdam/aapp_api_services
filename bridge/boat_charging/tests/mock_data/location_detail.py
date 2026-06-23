MOCK_RESPONSE = {
    "id": "2c0ccfb795d040e39136b7dd1d25f13e",
    "name": "AmsterdamBoatTest1",
    "address": "Isolatorweg 178",
    "city": "Amsterdam",
    "postalCode": "1234 AM",
    "coordinates": {"latitude": "52.327549", "longitude": "4.972519"},
    "openingTimes": {"twentyfourseven": True},
    "chargingStationsIds": ["VCPS-7BMY2", "VCPS-MX1VV", "VCPS-IFZTY"],
    "tariffId": "NLSGABCDEFGAOXJFEYABDEAJPNTOY",
    "tariff": {
        "id": "NLSGABCDEFGAOXJFEYABDEAJPNTOY",
        "energyPricePerKwh": 0.23,
        "chargingTimePricePerHour": 0.45,
        "parkingTimePricePerHour": 0.12,
        "flatFeePrice": 1.0,
        "standardFine": 1.0,
        "standardFineAfterHours": 24.0,
    },
    "chargingStations": [
        {
            "id": "VCPS-7BMY2",
            "status": "OFFLINE",
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
            "evses": [
                {
                    "id": 17,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "INOPERATIVE",
                    "connectors": [
                        {
                            "connectorId": 1,
                            "maxAmp": 1,
                            "voltage": 1,
                            "maxElectricPower": 22000,
                            "status": "INOPERATIVE",
                        }
                    ],
                }
            ],
        },
        {
            "id": "VCPS-IFZTY",
            "status": "OFFLINE",
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
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
            "locationId": "2c0ccfb795d040e39136b7dd1d25f13e",
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

MOCK_RESPONSE_WITH_TARIFF = {
    "id": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
    "name": "AmsterdamBoatTest3",
    "address": "Funenkade 7",
    "city": "Amsterdam",
    "postalCode": "1093 SJ",
    "coordinates": {"latitude": "52.366474", "longitude": "4.926436"},
    "openingTimes": {"twentyfourseven": False},
    "chargingStationsIds": ["VCPS-7BMY3"],
    "tariffId": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
    "tariff": {
        "id": "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
        "energyPricePerKwh": 0.23,
        "chargingTimePricePerHour": 0.45,
        "parkingTimePricePerHour": 0.12,
        "flatFeePrice": 1.0,
        "standardFine": 1.0,
        "standardFineAfterHours": 24.0,
    },
    "chargingStations": [
        {
            "id": "VCPS-7BMY3",
            "status": "OFFLINE",
            "locationId": "a9d9b42ce3eb4d8cbf50bb6aaeaa6357",
            "evses": [
                {
                    "id": 25,
                    "ocppEvseId": 1,
                    "evseId": "1",
                    "status": "OCCUPIED",
                    "substatus": "FINISHING",
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
        }
    ],
    "availableSockets": 0,
    "totalSockets": 1,
}
