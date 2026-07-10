MOCK_RESPONSE = {
    "result": "success",
    "data": {
        "client_product_id": 1004,
        "client_id": 1000,
        "payment_method": "DIRECT_DEBIT",
        "parent_client_product": None,
        "parent_permit_request": None,
        "address": {
            "id": 11000,
            "full_address": "Orteliusstraat 56-1, 1057BD AMSTERDAM",
        },
        "config": {
            "can_start_parking_session": True,
            "can_input_vrn": False,
            "can_activate_vrn": False,
            "can_select_zone": True,
            "has_time_balance": True,
            "has_money_balance": True,
            "has_visitor_account": True,
            "min_vrn": 0,
            "max_vrn": 0,
        },
        "handicap_card": {"type": None, "number": None, "ended_at": None},
        "permit": {
            "id": 476,
            "name": "Bezoekersparkeervergunning",
            "status": "ACTIVE",
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
                                    [4.896698965, 52.384741951],
                                    [4.896856962, 52.384531367],
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
        "request": {"id": 1010, "type": "permit_request"},
        "ssp": {
            "money_balance_amount": 998610,
            "time_balance_remaining_time": 507050,
            "time_balance_expires_at": "2026-09-30T21:59:59+00:00",
        },
        "validity": {
            "duration": 99,
            "duration_type": "lifetime",
            "started_at": "2026-05-03T17:51:41+00:00",
            "ended_at": "2125-05-03T21:59:59+00:00",
            "legal_at": None,
            "cancelled_at": None,
            "renewed_at": None,
        },
        "vrns": [],
    },
}
