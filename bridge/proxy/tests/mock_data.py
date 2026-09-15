from shapely.geometry import shape

ADDRESS_DATA = {
    "response": {
        "numFound": 585803,
        "start": 0,
        "maxScore": 3.4926538,
        "numFoundExact": True,
        "docs": [
            {
                "type": "weg",
                "woonplaatsnaam": "Weesp",
                "id": "weg-67c14f84f053f36864230e3d0c4ac06b",
                "centroide_ll": "POINT(5.04960914 52.30283261)",
                "straatnaam": "Diepenbroickpark",
                "score": 3.4926538,
            },
            {
                "type": "weg",
                "woonplaatsnaam": "Weesp",
                "id": "weg-fee00c735e2eb44c817a9f4d7ec12638",
                "centroide_ll": "POINT(5.04926746 52.30333625)",
                "straatnaam": "H.J.Hoflandlaan",
                "score": 3.491477,
            },
            {
                "type": "adres",
                "woonplaatsnaam": "Amsterdam",
                "id": "adr-b7c4344f08a82c116d29b4ff9d685bbc",
                "postcode": "1033KK",
                "centroide_ll": "POINT(4.8971361 52.4107674)",
                "nummeraanduiding_id": "0363200000245589",
                "huisnummer": 1,
                "straatnaam": "Pruimenstraat",
                "score": 5.32666,
            },
        ],
    }
}

POLLING_STATIONS_DATA = [
    {
        "id": 4049,
        "numbers": ["478"],
        "name": "10e Montessorischool De Meidoorn",
        "address1": "Chass�straat 59",
        "address2": "1057 JA Amsterdam",
        "position": {"lat": 52.369054951494, "lng": 4.8613880755879},
        "lastUpdate": {"state": 1, "time": None},
        "isOpen": False,
        "openingTimes": [[1761719400, 1761768000]],
        "categories": ["reading_aid", "disabled_parking"],
    },
    {
        "id": 4050,
        "numbers": ["428", "429"],
        "name": "2e Montessorischool Het Winterkoninkje",
        "address1": "Jan Pieter Heijestraat 45",
        "address2": "1053 GK Amsterdam",
        "position": {"lat": 52.365323215197, "lng": 4.8630032826713},
        "lastUpdate": {"state": 1, "time": None},
        "isOpen": False,
        "openingTimes": [[1761719400, 1761768000]],
        "categories": ["reading_aid", "disabled_parking"],
    },
    {
        "id": 4051,
        "numbers": ["113"],
        "name": "ABBS De Zuiderzee",
        "address1": "Brigantijnkade 51",
        "address2": "1086 VB Amsterdam",
        "position": {"lat": 52.36274279781, "lng": 4.9875257743206},
        "lastUpdate": {"state": 1, "time": None},
        "isOpen": False,
        "openingTimes": [[1761719400, 1761768000]],
        "categories": ["reading_aid", "disabled_parking"],
    },
    {
        "id": 4052,
        "numbers": ["722"],
        "name": "ABBS Het Gein",
        "address1": "Cornelis Aarnoutsstraat 80",
        "address2": "1106 ZG Amsterdam",
        "position": {"lat": 52.298771589873, "lng": 4.9934851244864},
        "lastUpdate": {"state": 1, "time": None},
        "isOpen": False,
        "openingTimes": [[1761719400, 1761768000]],
        "categories": ["reading_aid", "disabled_parking"],
    },
    {
        "id": 4053,
        "numbers": ["4"],
        "name": "Akhnaton",
        "address1": "Nieuwezijds Kolk 25",
        "address2": "1012 PV Amsterdam",
        "position": {"lat": 52.376143500633, "lng": 4.8941704196591},
        "lastUpdate": {"state": 1, "time": None},
        "isOpen": False,
        "openingTimes": [[1761719400, 1761768000]],
        "categories": ["reading_aid", "disabled_parking"],
    },
]

MOCK_POSTAL_AREA_SHAPES = {
    "1056": shape(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [4.8426, 52.3749],
                    [4.8426, 52.3696],
                    [4.8569, 52.3712],
                    [4.8672, 52.3725],
                    [4.8636, 52.3778],
                    [4.8461, 52.3752],
                    [4.8426, 52.3749],
                ]
            ],
        }
    )
}

AFVALSCHEIDINGSWIJZER = """0:{"a":"$@1","f":"","q":"","i":false,"b":"YJksOH9jv3dH7qkRJUDt1"}
1:{"total":3,"skip":0,"take":100,"searchTerm":"potgrond","language":"nl-NL","results":[{"identifier":"25f8b395-1793-4e96-9c27-e2d953118840","name":"Potgrond","route":{"path":"/alle-afvalproducten/tuin/grond/potgrond/"},"contentType":"synonymPage","fields":{"heroTitle":"Potgrond"},"score":0.4191785,"isSameForAllCultures":false},{"identifier":"9a3b6b52-8c6a-4465-bb9e-36471a4177ec","name":"Zak potgrond","route":{"path":"/alle-afvalproducten/plastic/grote-plastic-folieverpakking/zak-potgrond/"},"contentType":"synonymPage","fields":{"heroTitle":"Zak potgrond"},"score":0.30446377,"isSameForAllCultures":false},{"identifier":"663ef79c-d3f0-4411-bf54-3894d42057cf","name":"Potgrondzak","route":{"path":"/alle-afvalproducten/plastic/grote-plastic-folieverpakking/potgrondzak/"},"contentType":"synonymPage","fields":{"heroTitle":"Potgrondzak"},"score":0.11080852,"isSameForAllCultures":false}]}
"""