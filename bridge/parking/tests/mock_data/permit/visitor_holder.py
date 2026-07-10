MOCK_RESPONSE = {
    "client_product_id": 1234,
    "config": {
        "can_start_parking_session": True,
        "can_input_vrn": False,
        "can_activate_vrn": False,
        "can_select_zone": True,
        "has_time_balance": True,
        "has_money_balance": True,
        "has_visitor_account": True,
        "can_add_or_change_plate": False,
        "is_change_plate_webform": False,
        "is_add_plate_webform": False,
        "min_vrn": 0,
        "max_vrn": 0,
    },
    "permit": {
        "name": "Bezoekersparkeervergunning",
        "type": "visitor",
        "status": "ACTIVE",
        "usage_id": "BEZOEKP",
        "cost": None,
        "zone": "CE02E Centrum-2e",
        "zone_group": None,
        "geo_json": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [4.894837586, 52.388691854],
                                [4.895998882, 52.386040313],
                                [4.893663311, 52.388614597],
                                [4.894837586, 52.388691854],
                            ]
                        ],
                    },
                    "properties": {
                        "fill": "blue",
                        "stroke": "blue",
                        "fill-opacity": 0.5,
                        "popupContent": "Centrum 2a",
                        "stroke-width": 2,
                        "stroke-opacity": 1,
                    },
                },
            ],
        },
    },
    "ssp": {
        "time_balance_expires_at": "2026-06-30T21:59:59+00:00",
        "favorite_machine_number": 10528,
        "main_account": {
            "username": "12345678",
            "pin": "1234",
            "money_balance": 981287,
            "time_balance": 539486,
        },
        "visitor_account": {
            "username": "12345679",
            "pin": "1234",
            "time_balance": 3600,
        },
    },
    "validity": {
        "duration": 99,
        "duration_type": "lifetime",
        "started_at": "2025-12-12T23:00:00+00:00",
        "ended_at": "2124-12-13T22:59:59+00:00",
        "cancelled_at": None,
    },
    "vrns": [],
}
