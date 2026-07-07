MOCK_RESPONSE = {
    "result": "success",
    "data": {
        "client_product_id": 1000,
        "client_id": 1000,
        "payment_method": "DIRECT_DEBIT",
        "parent_client_product": None,
        "parent_permit_request": None,
        "address": {
            "id": 11000,
            "full_address": "Orteliusstraat 56-1, 1057BD AMSTERDAM",
        },
        "config": {
            "can_start_parking_session": False,
            "can_input_vrn": True,
            "can_activate_vrn": False,
            "can_select_zone": False,
            "has_time_balance": False,
            "has_money_balance": False,
            "has_visitor_account": False,
            "min_vrn": 1,
            "max_vrn": 1,
        },
        "handicap_card": {"type": None, "number": None, "ended_at": None},
        "permit": {
            "id": 352,
            "name": "Bewonersvergunning",
            "status": "ACTIVE",
            "cost": 31560,
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
                                    [4.896698965, 52.384741951],
                                ]  # truncated!
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
                    }
                ],
            },
        },
        "request": {"id": 1000, "type": "permit_request"},
        "ssp": {
            "money_balance_amount": None,
            "time_balance_remaining_time": None,
            "time_balance_expires_at": None,
        },
        "validity": {
            "duration": 6,
            "duration_type": "month",
            "started_at": "2026-05-03T17:51:41+00:00",
            "ended_at": "2026-11-03T22:59:59+00:00",
            "legal_at": None,
            "cancelled_at": None,
            "renewed_at": "2026-11-04T22:59:59+00:00",
        },
        "vrns": ["AB124C"],
    },
}
