MOCK_RESPONSE_NO_RATE = {
    "result": "success",
    "data": {
        "zone_id": 6,
        "zone_description": "Tariefzone 2 ma-za 09:00-24:00 zo 12:00-24:00",
        "time_frame_data": [
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 1200, "endTime": 2400}],
            [
                {"specialdayname": "ZONDAG", "specialdaydate": 20221226},
                {"specialdayname": "VRIJPARK", "specialdaydate": 20230427},
                {"specialdayname": "VRIJPARK", "specialdaydate": 20240427},
                {"specialdayname": "VRIJPARK", "specialdaydate": 20250426},
                {"specialdayname": "VRIJPARK", "specialdaydate": 20260427},
                {"specialdayname": "VRIJPARK", "specialdaydate": 20270427},
                {"specialdayname": "VRIJPARK", "specialdaydate": 20280427},
            ],
        ],
    },
}

MOCK_RESPONSE_SUNDAY_FREE = {
    "result": "success",
    "data": {
        "zone_id": 6,
        "zone_description": "Tariefzone 2 (€6,73) ma-za 09:00-24:00 zo 12:00-24:00",
        "time_frame_data": [
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [{"startTime": 900, "endTime": 2400}],
            [],
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
            [{"startTime": "0900", "endTime": "2059"}],
        ],
    },
}
