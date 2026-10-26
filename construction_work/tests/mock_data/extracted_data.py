MOCK_EXTRACTED_DATA = {
    "projects": [
        {
            "title": "Mock bridge project: Some work to be done",
            "changedDate": "2026-08-10T09:46:00",
            "publicationDate": "2021-11-24T13:00:00",
            "image": [
                {
                    "name": "mock-project-image.jpg",
                    "src": "/sites/default/files/mock-project-image.jpg",
                }
            ],
            "id": 101,
            "path": "https://example.invalid/mock-project",
            "summaryShort": "A short mock project summary.",
            "summaryIntroductory": None,
            "content": [
                {
                    "id": 201,
                    "rows": [
                        {
                            "content": [
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "id": 301,
                                    "contentIndication": "what",
                                    "content": "<h2>Wat</h2><p>Work on the bridge.</p>",
                                },
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "id": 302,
                                    "contentIndication": "where",
                                    "content": (
                                        "<h2>Waar</h2><p>At the mock canal.</p>"
                                    ),
                                },
                                {
                                    "__typename": "ParagraphDdsProgressList",
                                    "id": 303,
                                    "contentIndication": "when-timeline",
                                    "intro": "Mock project planning.",
                                    "items": [
                                        {
                                            "title": "2026",
                                            "description": "<p>Work starts.</p>",
                                            "initiallyCollapsed": False,
                                            "items": [],
                                        }
                                    ],
                                },
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "id": 304,
                                    "contentIndication": "contact",
                                    "content": (
                                        "<h2>Contact</h2><p><strong>Alex Example"
                                        "</strong><br>Project manager<br>"
                                        '<a href="mailto:alex@example.invalid">'
                                        "alex@example.invalid</a></p>"
                                    ),
                                },
                                {
                                    "id": 305,
                                    "contentIndication": None,
                                    "description": None,
                                    "mapDataset": [
                                        {
                                            "pointsOfInterest": [
                                                {
                                                    "location": {
                                                        "latitude": 52.37,
                                                        "longitude": 4.89,
                                                    }
                                                }
                                            ]
                                        }
                                    ],
                                    "title": "Mock bridge project",
                                },
                                {
                                    "__typename": "ParagraphDdsViews",
                                    "id": 501,
                                    "contentIndication": "news",
                                    "content": None,
                                    "title": "Mock project updates",
                                },
                            ]
                        }
                    ],
                }
            ],
        }
    ],
    "news_articles": {
        "501": [
            {
                "id": 601,
                "tag": [{"id": 701, "name": "Mock construction"}],
                "summaryShort": "A short mock article summary.",
                "title": "Mock project update",
                "changedDate": "2026-08-12T11:30:00",
                "publicationDate": "2026-08-11T08:15:00",
                "path": "https://example.invalid/mock-project-update",
                "image": [
                    {
                        "name": "mock-article-image.jpg",
                        "src": "/sites/default/files/mock-article-image.jpg",
                    }
                ],
                "content": [
                    {
                        "id": 801,
                        "rows": [
                            {
                                "content": [
                                    {
                                        "id": 901,
                                        "content": "<p>Mock article body.</p>",
                                    }
                                ]
                            }
                        ],
                    }
                ],
            }
        ]
    },
}

MOCK_NESTED_CONTENT_AND_SHARED_NEWS_EXTRACTED_DATA = {
    "projects": [
        {
            "id": 5,
            "title": "",
            "publicationDate": "2024-01-02T00:00:00+00:00",
            "changedDate": None,
            "content": [
                "not a grid",
                {
                    "rows": [
                        None,
                        {
                            "content": [
                                None,
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "content": "<p>Unmapped section</p>",
                                },
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "contentIndication": "contact",
                                    "content": "<strong>Unknown</strong>",
                                },
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "id": 12,
                                    "contentIndication": "contact",
                                    "content": (
                                        "<p><strong>Sam Example</strong><br/>Manager"
                                        '<br/><a href="tel:+31201234">Call</a></p>'
                                    ),
                                },
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "contentIndication": "unrecognized",
                                    "content": (
                                        '<h2>Waar</h2><p><a href="/route">Route</a></p>'
                                    ),
                                },
                                {
                                    "__typename": "ParagraphDdsProgressList",
                                    "intro": "Planning",
                                    "items": [
                                        {
                                            "title": "Stage one",
                                            "description": "First stage",
                                            "initiallyCollapsed": True,
                                            "items": [
                                                {
                                                    "title": "Substage",
                                                    "items": None,
                                                }
                                            ],
                                        }
                                    ],
                                },
                                {
                                    "__typename": "ParagraphDdsMapDataset",
                                    "mapDataset": [
                                        {"pointsOfInterest": [{"location": None}]},
                                        {
                                            "pointsOfInterest": [
                                                {
                                                    "location": {
                                                        "latitude": 52.3,
                                                        "longitude": 4.9,
                                                    }
                                                }
                                            ]
                                        },
                                    ],
                                },
                                {
                                    "__typename": "ParagraphDdsViews",
                                    "contentIndication": "news",
                                    "id": 700,
                                },
                            ]
                        },
                    ]
                },
            ],
        },
        {
            "id": 6,
            "content": [
                {
                    "rows": [
                        {
                            "content": [
                                {
                                    "__typename": "ParagraphDdsViews",
                                    "contentIndication": "news",
                                    "id": 700,
                                },
                                {
                                    "__typename": "ParagraphDdsMapDataset",
                                    "mapDataset": [],
                                },
                            ]
                        }
                    ]
                }
            ],
        },
    ],
    "news_articles": {
        700: [
            {
                "id": 901,
                "tag": {"name": "Notice"},
                "content": [
                    "not a grid",
                    {
                        "rows": [
                            None,
                            {
                                "content": [
                                    None,
                                    {"content": "<p>Article body</p>"},
                                    {"content": 42},
                                ]
                            },
                        ]
                    },
                ],
            },
            {
                "id": 901,
                "tag": {"name": "Notice"},
                "content": [
                    {
                        "rows": [
                            {
                                "content": [
                                    {"content": "<p>Duplicate article</p>"},
                                ]
                            }
                        ]
                    }
                ],
            },
            {"id": 902, "tag": []},
        ]
    },
}
