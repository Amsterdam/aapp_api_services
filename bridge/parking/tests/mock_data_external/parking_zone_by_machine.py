MOCK_RESPONSE_NO_RATE = {
    "result": "success",
    "data": {
        "zone_id": 100000000,
        "zone_description": "Tariefzone 1 ma-zo 00-24 (T11V)",
        "time_frame_data": [
            [{"startTime": "0000", "endTime": "2359"}],
            [{"startTime": "0000", "endTime": "2359"}],
            [{"startTime": "0000", "endTime": "2359"}],
            [{"startTime": "0000", "endTime": "2359"}],
            [{"startTime": "0000", "endTime": "2359"}],
            [{"startTime": "0000", "endTime": "2359"}],
            [{"startTime": "0000", "endTime": "2359"}],
        ],
    },
}

MOCK_RESPONSE_WITH_RATE = {
    "result": "success",
    "data": {
        "zone_id": 100000000,
        "zone_description": "Tariefzone 2 (€6,73) ma-za 09:00-21:00",
        "time_frame_data": [
            [{"startTime": "0900", "endTime": "2059"}],
            [{"startTime": "0900", "endTime": "2059"}],
            [{"startTime": "0900", "endTime": "2059"}],
            [{"startTime": "0900", "endTime": "2059"}],
            [{"startTime": "0900", "endTime": "2059"}],
            [{"startTime": "0900", "endTime": "2059"}],
        ],
    },
}
