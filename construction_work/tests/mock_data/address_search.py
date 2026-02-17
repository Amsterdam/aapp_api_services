MOCK_DATA_SINGLE = {
    "@odata.count": 1,
    "@search.facets": {
        "openbareruimteNaam": [{"value": "Straatnaam", "count": 1}],
        "postcode": [{"value": "1023AB", "count": 1}],
    },
    "value": [
        {
            "@search.score": 16.283151,
            "@search.highlights": {
                "huisnummerStr": ["<em>1</em>"],
                "openbareruimteNaam": ["<em>Straatnaam</em>"],
            },
            "identificatie": "123",
            "woonplaatsNaam": "Amsterdam",
            "openbareruimteNaam": "Straatnaam",
            "postcode": "1023AB",
            "huisnummer": 1,
            "huisletter": None,
            "huisnummertoevoeging": None,
            "latitude": 52.395811189,
            "longitude": 4.952262942,
        }
    ],
}


MOCK_DATA_MULTIPLE = {
    "@odata.count": 2,
    "@search.facets": {
        "openbareruimteNaam": [{"value": "Straatnaam", "count": 2}],
        "postcode": [
            {"value": "1023AB", "count": 2},
        ],
    },
    "value": [
        {
            "@search.score": 11.314914,
            "@search.highlights": {
                "huisnummerStr": ["<em>1</em>"],
                "openbareruimteNaam": ["<em>Straatnaam</em>"],
            },
            "identificatie": "123",
            "woonplaatsNaam": "Amsterdam",
            "openbareruimteNaam": "Straatnaam",
            "postcode": "1023AB",
            "huisnummer": 1,
            "huisletter": None,
            "huisnummertoevoeging": "1",
            "latitude": 52.358355832,
            "longitude": 4.911484561,
        },
        {
            "@search.score": 11.314914,
            "@search.highlights": {
                "huisnummerStr": ["<em>1</em>"],
                "openbareruimteNaam": ["<em>Straatnaam</em>"],
            },
            "identificatie": "1234",
            "woonplaatsNaam": "Amsterdam",
            "openbareruimteNaam": "Straatnaam",
            "postcode": "1023AB",
            "huisnummer": 1,
            "huisletter": None,
            "huisnummertoevoeging": "2",
            "latitude": 52.358355832,
            "longitude": 4.911484561,
        },
    ],
}

MOCK_DATA_NONE = {
    "@odata.count": 0,
    "@search.facets": {"openbareruimteNaam": [], "postcode": []},
    "value": [],
}
