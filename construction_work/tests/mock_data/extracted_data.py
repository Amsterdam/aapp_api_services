MOCK_EXTRACTED_DATA = {
    "projects": [
        {
            "title": "Mock bridge project",
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
