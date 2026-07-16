MOCK_DATA = {
    "AFIS": {
        "content": {
            "isKnown": True,
            "businessPartnerIdEncrypted": "oEDLgvm3qbMiRRykkw5fxcILSfrv6QmKfJxKsJFHgzKuye257YVS0ZXsPBZLZp6UymNcoqJ0tA2dJeLdssP82tPwRndgm2DEaavbIW8FP-OqIg7Yk-gCHmYp9Gl25JQ-YqioStIUvc9UjoDZn-HDzg",
            "facturen": {
                "open": {
                    "count": 69,
                    "state": "open",
                    "facturen": [
                        {
                            "id": "2600123120-2600123120-2026-05-07t000000",
                            "afzender": "SDN Begraafplaats DN",
                            "datePublished": "2026-05-07T00:00:00",
                            "datePublishedFormatted": "07 mei 2026",
                            "paymentDueDate": "2026-05-07T00:00:00",
                            "paymentDueDateFormatted": "07 mei 2026",
                            "debtClearingDate": None,
                            "debtClearingDateFormatted": None,
                            "amountPayed": "0.01",
                            "amountPayedFormatted": "€ 0,01",
                            "amountOriginal": "0.01",
                            "amountOriginalFormatted": "€ 0,01",
                            "factuurNummer": "2600123120",
                            "factuurDocumentId": "2600123120",
                            "status": "openstaand",
                            "statusDescription": "€ 0,01 betaal nu",
                            "paylink": "https://betalingen.amsterdam.nl/pay/1863664052/bca84743e6c11e9943390265f6e00f634a23ce2f",
                            "eMandateId": "",
                            "documentDownloadLink": "https://test.mijn.amsterdam.nl/api/v1/services/afis/facturen/document?id=fBlxgVnnl91YWAyrXJZy7CIEyjT8MAtCOVK7Oh8pVGpMaQFG1rKof_8UAzKgtAO8RQZ-3AXRC9OsUrFeTfWd8A",
                            "link": {
                                "to": "/facturen-en-betalen/factuur/open/2600123120",
                                "title": "Factuur 2600123120",
                            },
                        },
                        {
                            "id": "2600123139-2600123139-2026-05-07t000000",
                            "afzender": "WP Sociaal Werk",
                            "datePublished": "2026-05-07T00:00:00",
                            "datePublishedFormatted": "07 mei 2026",
                            "paymentDueDate": "2026-05-07T00:00:00",
                            "paymentDueDateFormatted": "07 mei 2026",
                            "debtClearingDate": None,
                            "debtClearingDateFormatted": None,
                            "amountPayed": "0.01",
                            "amountPayedFormatted": "€ 0,01",
                            "amountOriginal": "0.01",
                            "amountOriginalFormatted": "€ 0,01",
                            "factuurNummer": "2600123139",
                            "factuurDocumentId": "2600123139",
                            "status": "factuur-in-termijnen",
                            "statusDescription": "€ 0,01 wordt automatisch van uw rekening afgeschreven. <br><strong>Let op! deze incassomachtiging is gestopt.</strong>",
                            "paylink": None,
                            "eMandateId": "100000000996",
                            "documentDownloadLink": "https://test.mijn.amsterdam.nl/api/v1/services/afis/facturen/document?id=R_pW9jnz-tFBbEX8BGN1FvLjqtEnXdypzmZw06SPIpvk3Ir34lQZDJy1XNCDu37EjHNGee3a309Pm2b1tdR5pg",
                            "link": {
                                "to": "/facturen-en-betalen/factuur/open/2600123139",
                                "title": "Factuur 2600123139",
                            },
                        },
                    ],
                },
                "afgehandeld": {
                    "count": 1,
                    "state": "afgehandeld",
                    "facturen": [
                        {
                            "id": "2600013164-2600013164-2026-01-01t000000",
                            "afzender": "GO Erfpacht en Uitgi",
                            "datePublished": "2025-11-26T00:00:00",
                            "datePublishedFormatted": "26 november 2025",
                            "paymentDueDate": "2026-01-01T00:00:00",
                            "paymentDueDateFormatted": "01 januari 2026",
                            "debtClearingDate": "2026-01-01T00:00:00",
                            "debtClearingDateFormatted": "01 januari 2026",
                            "amountPayed": "316.57",
                            "amountPayedFormatted": "€ 316,57",
                            "amountOriginal": "316.57",
                            "amountOriginalFormatted": "€ 316,57",
                            "factuurNummer": "2600013164",
                            "factuurDocumentId": "2600013164",
                            "status": "betaald",
                            "statusDescription": "€ 316,57 betaald op 01 januari 2026",
                            "paylink": "https://betalingen.amsterdam.nl/pay/1758727321/a43e053f0d4c8b87e1b0d60788e3a7de0fa79dc7",
                            "eMandateId": "",
                            "documentDownloadLink": "https://test.mijn.amsterdam.nl/api/v1/services/afis/facturen/document?id=XUiqToAynlKaoBWh-Wz4NqgsLfgBjjq1bMkCyEyZLI2VPWWfGMHLNTQQNfEiaFJj5y9_YrNOT7EeGH1FdSYh9g",
                            "link": {
                                "to": "/facturen-en-betalen/factuur/afgehandeld/2600013164",
                                "title": "Factuur 2600013164",
                            },
                        }
                    ],
                },
                "overgedragen": {"count": 0, "state": "overgedragen", "facturen": []},
            },
        },
        "status": "OK",
    },
    "KLACHTEN": {"content": [], "status": "OK"},
    "KREFIA": {
        "content": {
            "deepLinks": [
                {
                    "displayStatus": "Lopend",
                    "link": {
                        "to": "https://krefia-acceptatie.amsterdam.nl/inloggen-fibu",
                        "title": "Ga naar budgetbeheer",
                    },
                    "type": "budgetbeheer",
                }
            ]
        },
        "status": "OK",
    },
    "KVK": {"content": None, "status": "OK"},
    "MILIEUZONE": {
        "content": {
            "isKnown": False,
            "url": "https://ontheffingen-acc.amsterdam.nl/publiek/aanvragen",
        },
        "status": "OK",
    },
    "WMO": {"content": [], "status": "OK"},
    "WPI_AANVRAGEN": {"content": [], "status": "OK"},
    "WPI_BBZ": {
        "content": [
            {
                "about": "Bbz",
                "dateEnd": None,
                "datePublished": "2026-01-20T16:36:12+01:00",
                "dateStart": "2021-09-22T00:00:00+02:00",
                "decision": None,
                "id": "2542b4b99f89ffec22ee61571981a47c",
                "statusId": "informatieOntvangen",
                "steps": [
                    {
                        "datePublished": "2021-09-22T00:00:00+02:00",
                        "documents": [
                            {
                                "datePublished": "2021-09-22T00:00:00+02:00",
                                "dcteId": "844",
                                "id": "400000493",
                                "title": "Aanvraag Bbz\n22 september 2021 00:00",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=INcwSEUo9SN6ic_PGhWs-O4GxLEvzrnm6kX2UwIRkHYESGH3gqJQzhq05JMhvzTlZnNsm2ZyIbHGaLg5Xny4yg&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2021-09-22T00:00:00+02:00",
                                "dcteId": "844",
                                "id": "400000492",
                                "title": "Aanvraag Bbz\n22 september 2021 00:00",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=XanuWqc9SyioSizirv6UwmkYeRUbTTNb0KZjasbPDNctAxQGTwY5UxhXSJhP4O-FAEnPqXRoRBlzWNi1f7P30g&isBulk=True&isDms=False",
                            },
                        ],
                        "id": "aanvraag",
                        "status": "Aanvraag",
                        "isActive": False,
                        "isChecked": True,
                        "description": "<p>Wij hebben uw aanvraag Bbz ontvangen. Het kan zijn dat er meer informatie en tijd nodig is om uw aanvraag te behandelen. Bekijk de aanvraag voor meer details.</p>",
                    },
                    {
                        "datePublished": "2023-05-11T11:23:39+02:00",
                        "documents": [
                            {
                                "datePublished": "2023-05-11T11:23:39+02:00",
                                "dcteId": "1538",
                                "id": "400000708",
                                "title": "Bbz: informatie doorgeven",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=qDR_C7cJ8nR-XAvhK1JMiQymjFmllqZFgBcYjaAAJjzgP69JHNBNZnbgjWI2pJLvZpyuWVjxDrdjM-4HPjxL3w&isBulk=True&isDms=False",
                            }
                        ],
                        "id": "informatieOntvangen",
                        "status": "Informatie ontvangen",
                        "isActive": False,
                        "isChecked": True,
                        "description": "<p>Wij hebben uw formulier 'Bbz: informatie doorgeven' ontvangen op 11 mei om 11.23 uur. Het kan zijn dat er meer informatie en tijd nodig is om uw Bbz-uitkering definitief te kunnen berekenen. Bekijk het formulier voor meer details.</p><p>Wij maken een definitieve berekening van uw Bbz-uitkering en sturen u een besluit. We proberen dit binnen 3 maanden te doen. Het kan langer duren doordat het nog erg druk is op onze afdeling.</p>",
                    },
                    {
                        "datePublished": "2026-01-20T16:36:12+01:00",
                        "documents": [
                            {
                                "datePublished": "2026-01-20T16:36:12+01:00",
                                "dcteId": "1538",
                                "id": "23068535",
                                "title": "Bbz: informatie doorgeven",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=ICH-BEH3n67-bDMcNGDLFo32qavDXWfyc6g3Fue7O8rTv_cL48s8jxs6O_z3sK3_NoM_0HUTr7B_L9K6AP6REA&isBulk=True&isDms=False",
                            }
                        ],
                        "id": "informatieOntvangen",
                        "status": "Informatie ontvangen",
                        "isActive": True,
                        "isChecked": True,
                        "description": "<p>Wij hebben uw formulier 'Bbz: informatie doorgeven' ontvangen op 20 januari om 16.36 uur. Het kan zijn dat er meer informatie en tijd nodig is om uw Bbz-uitkering definitief te kunnen berekenen. Bekijk het formulier voor meer details.</p><p>Wij maken een definitieve berekening van uw Bbz-uitkering en sturen u een besluit. We proberen dit binnen 3 maanden te doen. Het kan langer duren doordat het nog erg druk is op onze afdeling.</p>",
                    },
                ],
                "title": "Bbz",
                "link": {
                    "to": "/inkomen/bbz/1/2542b4b99f89ffec22ee61571981a47c",
                    "title": "Bekijk uw aanvraag",
                },
                "displayStatus": "Informatie ontvangen",
                "dateStartFormatted": "22 september 2021",
                "dateEndFormatted": None,
            }
        ],
        "status": "OK",
    },
    "WPI_SPECIFICATIES": {
        "content": {"jaaropgaven": [], "uitkeringsspecificaties": []},
        "status": "OK",
    },
    "WPI_TONK": {
        "content": [
            {
                "about": "TONK",
                "dateEnd": None,
                "datePublished": "2021-07-02T23:44:31+02:00",
                "dateStart": "2021-02-24T17:42:11+01:00",
                "decision": None,
                "id": "2f4079a4ea1d6c6355eea447e673888d",
                "statusId": "aanvraag",
                "steps": [
                    {
                        "datePublished": "2021-02-24T17:42:11+01:00",
                        "documents": [
                            {
                                "datePublished": "2021-02-24T17:42:11+01:00",
                                "dcteId": "802",
                                "id": "400000440",
                                "title": "Aanvraag TONK\n24 februari 2021 17:42",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=28GPHEZODvFmSm6_NT4Si6jMTSeCkD5WD87hwlUeEs_XbACsFOK37x_c2Ez6bPnEiJ6QArNsb_m6kADLc495_w&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2021-02-26T14:10:43+01:00",
                                "dcteId": "802",
                                "id": "400000561",
                                "title": "Aanvraag TONK\n26 februari 2021 14:10",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=UCXiCryvfTl0aTn250aQ1j5U1XcRzA7__HA_bL2YyXRmm70m7yO61foGAqSZkB9N0pIb2UCEN8ULvzqh9Xsy8Q&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2021-07-02T23:44:31+02:00",
                                "dcteId": "802",
                                "id": "400000782",
                                "title": "Aanvraag TONK\n02 juli 2021 23:44",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=JOvjsxoAVehf8Cm03DbgFCgEqId6I_IpAnGfE0hBKd6wj0kwLEDb7q0ZXQfbZ7DYnpkm3AmwvVTtqJ6QaTRrAg&isBulk=True&isDms=False",
                            },
                        ],
                        "id": "aanvraag",
                        "productSpecific": "uitkering",
                        "status": "Aanvraag",
                        "isActive": True,
                        "isChecked": True,
                        "description": "<p>\n        Wij hebben uw aanvraag TONK ontvangen.\n      </p>",
                    }
                ],
                "title": "TONK",
                "link": {
                    "to": "/inkomen/tonk/1/2f4079a4ea1d6c6355eea447e673888d",
                    "title": "Bekijk uw aanvraag",
                },
                "displayStatus": "Aanvraag",
                "dateStartFormatted": "24 februari 2021",
                "dateEndFormatted": None,
            }
        ],
        "status": "OK",
    },
    "WPI_TOZO": {
        "content": [
            {
                "about": "Tozo 1",
                "dateEnd": None,
                "datePublished": "2022-06-24T12:20:54+02:00",
                "dateStart": "2020-03-28T10:33:49+01:00",
                "decision": None,
                "id": "cc1cecbe5bf7f201bf8a2972f47a5a9d",
                "statusId": "aanvraag",
                "steps": [
                    {
                        "datePublished": "2020-03-28T10:33:49+01:00",
                        "documents": [
                            {
                                "datePublished": "2020-03-28T10:33:49+01:00",
                                "dcteId": "770",
                                "id": "400001032",
                                "title": "Aanvraag Tozo 1\n28 maart 2020 10:33",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=5AChvH3gudFI4GX4Eltdyg0YCxgGbTz8f5Yrz32WmwRIbPqmaCW0EkiTy4Pr3hg9EFrSRP11GWYFrII_zZkmjQ&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2020-03-28T10:33:49+01:00",
                                "dcteId": "756",
                                "id": "400000910",
                                "title": "Aanvraag Tozo 1\n28 maart 2020 10:33",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=J22QK3S9M79xn6-GqtyX6alON7kMI5RqIYD__x-DtYhyv6oQuHIB2C9qVaGHpcSNRg5brJXdoXE_a5RJCLf9Ig&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2022-06-24T12:20:54+02:00",
                                "dcteId": "770",
                                "id": "400000645",
                                "title": "Aanvraag Tozo 1\n24 juni 2022 12:20",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=teCkjZmRI9YUanchE-CVmq4nPe9poHNZI37iSYD9SMtbFa7JvLM5Qh1jMxj75i31Ts4q09led3ZGunhD2MNlJA&isBulk=True&isDms=False",
                            },
                        ],
                        "id": "aanvraag",
                        "status": "Aanvraag",
                        "isActive": True,
                        "isChecked": True,
                        "description": "<p>\n        Wij hebben uw aanvraag Tozo 1 ontvangen.\n      </p>",
                    }
                ],
                "title": "Tozo 1 (aangevraagd voor 1 juni 2020)",
                "link": {
                    "to": "/inkomen/tozo/1/cc1cecbe5bf7f201bf8a2972f47a5a9d",
                    "title": "Bekijk uw aanvraag",
                },
                "displayStatus": "Aanvraag",
                "dateStartFormatted": "28 maart 2020",
                "dateEndFormatted": None,
            },
            {
                "about": "Tozo 2",
                "dateEnd": None,
                "datePublished": "2021-06-17T13:23:54+02:00",
                "dateStart": "2020-06-04T15:06:17+02:00",
                "decision": None,
                "id": "44bcc9f2ab0cd9bd01492ec8a38e4702",
                "statusId": "inkomstenwijziging",
                "steps": [
                    {
                        "datePublished": "2020-06-04T15:06:17+02:00",
                        "documents": [
                            {
                                "datePublished": "2020-06-04T15:06:17+02:00",
                                "dcteId": "777",
                                "id": "400000964",
                                "title": "Aanvraag Tozo 2\n04 juni 2020 15:06",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=uOLSK-yM1AoShEOsfnrAtJnXX1ApbhnAhA6NbqcqE7BUiVhbri-lGdP2YOZXxvHXAULklWhzH29lirCO_KSHqw&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2020-07-15T20:17:22+02:00",
                                "dcteId": "777",
                                "id": "400000988",
                                "title": "Aanvraag Tozo 2\n15 juli 2020 20:17",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=NOeMvLzriDUwqfQHzZmgtbsKqgces_dh4Fb6fhlj2-kbuQ-N92qfm5_sVAZDCyLa6kBIHS89NqUe8CZFawcSbA&isBulk=True&isDms=False",
                            },
                            {
                                "datePublished": "2020-09-14T15:49:40+02:00",
                                "dcteId": "777",
                                "id": "400000989",
                                "title": "Aanvraag Tozo 2\n14 september 2020 15:49",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=QbbRARo1fRT9vHIEwM-GUOhCCQnJ4DlS1cD2m39h9KD7UssgVPAreleAm2N9Vs-xFLOZ3bQbNDm2WYdtwPC89A&isBulk=True&isDms=False",
                            },
                        ],
                        "id": "aanvraag",
                        "status": "Aanvraag",
                        "isActive": False,
                        "isChecked": True,
                        "description": "<p>\n        Wij hebben uw aanvraag Tozo 2 ontvangen.\n      </p>",
                    },
                    {
                        "datePublished": "2020-12-17T14:57:35+01:00",
                        "documents": [
                            {
                                "datePublished": "2020-12-17T14:57:35+01:00",
                                "dcteId": "790",
                                "id": "400000599",
                                "title": "Wijziging inkomsten",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=mf1Dij4sP3qYTn4PfWvuL2dGzWRyaNI68dKiJ2ZRHV5KlMgebLwbM8fwujSWj9wgzD8K3uHrA9Jg9oBnpP83nA&isBulk=True&isDms=False",
                            }
                        ],
                        "id": "inkomstenwijziging",
                        "status": "Wijziging inkomsten",
                        "isActive": False,
                        "isChecked": True,
                        "description": "\n    <p>Wij hebben een wijziging van uw inkomsten voor Tozo 2 (aangevraagd vanaf 1 juni 2020) ontvangen op 17 december om 14.57 uur</p>\n    <p>De wijziging wordt zo snel mogelijk verwerkt. Als u een nabetaling krijgt dan ziet u dat op uw uitkeringsspecificatie. Als u moet terugbetalen dan ontvangt u daarover een besluit per post.</p>",
                    },
                    {
                        "datePublished": "2020-12-18T14:27:08+01:00",
                        "documents": [
                            {
                                "datePublished": "2020-12-18T14:27:08+01:00",
                                "dcteId": "790",
                                "id": "400000284",
                                "title": "Wijziging inkomsten",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=2GW8jcylvtme2L2VQf9rVBLi3_QLBK1S9btLgouA3JU3uKPHHMKpdadm4aX4-7EpymbztQaYtpupqByq3OPQ9A&isBulk=True&isDms=False",
                            }
                        ],
                        "id": "inkomstenwijziging",
                        "status": "Wijziging inkomsten",
                        "isActive": False,
                        "isChecked": True,
                        "description": "\n    <p>Wij hebben een wijziging van uw inkomsten voor Tozo 2 (aangevraagd vanaf 1 juni 2020) ontvangen op 18 december om 14.27 uur</p>\n    <p>De wijziging wordt zo snel mogelijk verwerkt. Als u een nabetaling krijgt dan ziet u dat op uw uitkeringsspecificatie. Als u moet terugbetalen dan ontvangt u daarover een besluit per post.</p>",
                    },
                    {
                        "datePublished": "2021-06-17T13:23:54+02:00",
                        "documents": [
                            {
                                "datePublished": "2021-06-17T13:23:54+02:00",
                                "dcteId": "790",
                                "id": "400000630",
                                "title": "Wijziging inkomsten",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=YFA1YGLVlHPE34zcRPvKI_0cnATPqSYFDv6qYtoMUnNvkznh5Qud6WykHAnNHnVNPtJecsBy8XJoYwsgjY6V7Q&isBulk=True&isDms=False",
                            }
                        ],
                        "id": "inkomstenwijziging",
                        "status": "Wijziging inkomsten",
                        "isActive": True,
                        "isChecked": True,
                        "description": "\n    <p>Wij hebben een wijziging van uw inkomsten voor Tozo 2 (aangevraagd vanaf 1 juni 2020) ontvangen op 17 juni om 13.23 uur</p>\n    <p>De wijziging wordt zo snel mogelijk verwerkt. Als u een nabetaling krijgt dan ziet u dat op uw uitkeringsspecificatie. Als u moet terugbetalen dan ontvangt u daarover een besluit per post.</p>",
                    },
                ],
                "title": "Tozo 2 (aangevraagd vanaf 1 juni 2020)",
                "link": {
                    "to": "/inkomen/tozo/2/44bcc9f2ab0cd9bd01492ec8a38e4702",
                    "title": "Bekijk uw aanvraag",
                },
                "displayStatus": "Wijziging inkomsten",
                "dateStartFormatted": "04 juni 2020",
                "dateEndFormatted": None,
            },
            {
                "about": "Tozo 5",
                "dateEnd": None,
                "datePublished": "2021-07-01T00:00:00+02:00",
                "dateStart": "2021-07-01T00:00:00+02:00",
                "decision": None,
                "id": "d3de4ce5a2aaf2cdcaa273baee43b1f2",
                "statusId": "aanvraag",
                "steps": [
                    {
                        "datePublished": "2021-07-01T00:00:00+02:00",
                        "documents": [
                            {
                                "datePublished": "2021-07-01T00:00:00+02:00",
                                "dcteId": "837",
                                "id": "400000866",
                                "title": "Aanvraag Tozo 5\n01 juli 2021 00:00",
                                "url": "https://test.mijn.amsterdam.nl/api/v1/services/wpi/document?id=seNKa2dKWx_0nzgf8iL5Wcz4Du_zTkH1vVYpzWLZpxYRNm8tuJ7LBAM3AhDz82KfjOg-pSNpOtcZbCv0IpIsFQ&isBulk=True&isDms=False",
                            }
                        ],
                        "id": "aanvraag",
                        "status": "Aanvraag",
                        "isActive": True,
                        "isChecked": True,
                        "description": "<p>\n        Wij hebben uw aanvraag Tozo 5 ontvangen.\n      </p>",
                    }
                ],
                "title": "Tozo 5 (aangevraagd vanaf 1 juli 2021)",
                "link": {
                    "to": "/inkomen/tozo/5/d3de4ce5a2aaf2cdcaa273baee43b1f2",
                    "title": "Bekijk uw aanvraag",
                },
                "displayStatus": "Aanvraag",
                "dateStartFormatted": "01 juli 2021",
                "dateEndFormatted": None,
            },
        ],
        "status": "OK",
    },
    "KTO": {
        "content": {
            "version": 1,
            "createdAt": "2026-01-20T14:51:03.230267+01:00",
            "activeFrom": "2026-01-20T14:50:40+01:00",
            "questions": [
                {
                    "id": 3,
                    "questionText": "Wat vindt u van deze pagina?",
                    "description": "Aantal sterren",
                    "questionType": "numeric",
                    "required": False,
                    "maxCharacters": 5,
                },
                {
                    "id": 2,
                    "questionText": "Heeft u nog een tip of compliment voor ons?",
                    "description": "Feedback vrij invul",
                    "questionType": "textarea",
                    "required": False,
                    "maxCharacters": 300,
                },
                {
                    "id": 1,
                    "questionText": "Uw e-mailadres (niet verplicht)",
                    "description": "E-mail",
                    "questionType": "email",
                    "required": False,
                    "maxCharacters": 0,
                },
            ],
        },
        "status": "OK",
    },
}
