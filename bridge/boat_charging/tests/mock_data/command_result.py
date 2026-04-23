MOCK_RESPONSE_NOT_RESPOND = {
    "results": [{"chargingStationId": "VCPS-7BMY3"}],
    "commandTime": "2026-04-22T12:10:54.429645Z",
}

MOCK_RESPONSE_NOT_CONFIRM = {
    "results": [{"chargingStationId": "VCPS-7BMY3"}],
    "commandTime": "2026-04-22T12:10:54.429645Z",
    "resultTime": "2026-04-22T12:10:54.429645Z",
}

MOCK_RESPONSE_REJECTED = {
    "results": [{"chargingStationId": "VCPS-7BMY3"}],
    "commandResult": {"status": "REJECTED"},
    "commandTime": "2026-04-22T12:10:54.429645Z",
    "resultTime": "2026-04-22T12:10:54.429645Z",
}

MOCK_RESPONSE_ACCEPTED = {
    "results": [{"chargingStationId": "VCPS-7BMY3"}],
    "commandResult": {"status": "ACCEPTED"},
    "commandTime": "2026-04-22T12:10:54.429645Z",
    "resultTime": "2026-04-22T12:10:54.429645Z",
}
