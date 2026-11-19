from copy import deepcopy

from django.test import SimpleTestCase, override_settings

from construction_work.etl.transform_data import (
    _transform_contact_content,
    _transform_project,
    transform_data,
)
from construction_work.tests.mock_data import extracted_data


@override_settings(
    TIME_ZONE="UTC",
    DVO_URL="https://source.example.invalid/graphql",
)
class TransformDataTestCase(SimpleTestCase):
    def test_transforms_extraction_shape_for_ingestion(self):
        extracted_payload = deepcopy(extracted_data.MOCK_DATA)

        result = transform_data(extracted_payload)

        self.assertEqual(extracted_payload, extracted_data.MOCK_DATA)
        self.assertEqual(
            [project["id"] for project in result["projects"]],
            [project["id"] for project in extracted_data.MOCK_DATA["projects"]],
        )
        self.assertEqual(
            [contact["name"] for contact in result["projects"][0]["contacts"]],
            ["Naam Achternaam", "Jane Smith", "Sarah Johnson"],
        )
        self.assertEqual(
            {article["id"]: article["projectIds"] for article in result["articles"]},
            {10017: [13452], 17549: [13447]},
        )
        self.assertEqual(
            result["projects"][0]["image"],
            {
                "id": None,
                "url": "https://source.example.invalid/sites/default/files/pages/955394/lammetjes.jpg",
                "alt": "An example image",
                "description": None,
            },
        )
        self.assertEqual(
            result["articles"][0]["image"]["url"],
            "https://source.example.invalid/sites/default/files/pages/1084359/image-ab.jpg",
        )

    def test_handles_missing_images_and_news_views(self):
        result = transform_data(
            {
                "projects": [
                    {
                        "id": 1,
                        "title": "No news",
                        "path": "https://example.invalid/no-news",
                        "changedDate": "2026-08-10T09:46:00",
                        "publicationDate": "2021-11-24T13:00:00",
                        "content": [],
                    }
                ],
                "news_articles": {},
                "work_articles": {},
            }
        )

        self.assertEqual(result["articles"], [])
        self.assertIsNone(result["projects"][0]["image"])
        self.assertIsNone(result["projects"][0]["timeline"]["title"])

    def test_accepts_empty_extraction_result(self):
        self.assertEqual(
            transform_data({"projects": [], "news_articles": {}, "work_articles": {}}),
            {"projects": [], "articles": []},
        )

    def test_transforms_shared_news_articles_for_multiple_projects(self):
        extracted_payload = deepcopy(extracted_data.MOCK_DATA)
        second_project = deepcopy(extracted_payload["projects"][0])
        second_project["id"] = 13453
        extracted_payload["projects"].append(second_project)

        result = transform_data(extracted_payload)

        self.assertEqual(
            {article["id"]: article["projectIds"] for article in result["articles"]},
            {10017: [13452, 13453], 17549: [13447]},
        )

    def test_transform_contact_content(self):

        block = {
            "__typename": "ParagraphDdsRichText",
            "id": 19989,
            "contentIndication": "contact",
            "content": '<h2>Contact</h2><p><strong>Voornaam Achternaam</strong><br>Position A<br>Extra info<br><a href="mailto:project.osdorpplein@amsterdam.nl">project.osdorpplein@amsterdam.nl</a></p><p><strong>Jane Smith</strong><br>Gebiedsmakelaar wonen<br>Voor vragen over wonen in de buurt, of als u wilt meedenken<br><a href="mailto:jane.smith@amsterdam.nl">jane.smith@amsterdam.nl</a></p><p><strong>Sarah Names</strong><br>Gebiedsmakelaar winkelgebied<br>Voor vragen over het winkelgebied, of als u wilt meedenken<br><a href="mailto:sarah.names@amsterdam.nl">sarah.names@amsterdam.nl</a></p>',
        }

        contacts, remaining_body = _transform_contact_content(block["content"])

        self.assertEqual(len(contacts), 3)
        self.assertEqual(remaining_body, "")
        self.assertTrue(all("id" not in contact for contact in contacts))
        self.assertEqual(contacts[0]["name"], "Voornaam Achternaam")
        self.assertEqual(contacts[0]["email"], "project.osdorpplein@amsterdam.nl")
        self.assertEqual(contacts[0]["position"], "Position A")
        self.assertEqual(contacts[0]["extra"], "Extra info")
        self.assertEqual(contacts[1]["name"], "Jane Smith")
        self.assertEqual(contacts[1]["email"], "jane.smith@amsterdam.nl")
        self.assertEqual(contacts[1]["position"], "Gebiedsmakelaar wonen")
        self.assertEqual(
            contacts[1]["extra"],
            "Voor vragen over wonen in de buurt, of als u wilt meedenken",
        )
        self.assertEqual(contacts[2]["name"], "Sarah Names")
        self.assertEqual(contacts[2]["email"], "sarah.names@amsterdam.nl")
        self.assertEqual(contacts[2]["position"], "Gebiedsmakelaar winkelgebied")
        self.assertEqual(
            contacts[2]["extra"],
            "Voor vragen over het winkelgebied, of als u wilt meedenken",
        )

    def test_contact_section_keeps_intro_separate_from_contact_details(self):
        project = {
            "id": 1,
            "title": "Project",
            "content": [
                {
                    "rows": [
                        {
                            "content": [
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "contentIndication": "contact",
                                    "content": (
                                        '<div class="dds-prose"><h2 class="dds-heading '
                                        'dds-heading--2">Contact</h2><p class="dds-paragraph">'
                                        "Inloop voor vragen: elke laatste dinsdag van de "
                                        "maand van 15.00 tot 17.00 uur, in InfoStek, "
                                        "Buikslotermeerplein 13b</p><p class="
                                        '"dds-paragraph"><strong>Projectteam '
                                        'Buikslotermeerplein</strong><br><a href="mailto:'
                                        'buikslotermeerplein@amsterdam.nl" class="dds-link">'
                                        "buikslotermeerplein@amsterdam.nl</a></p></div>"
                                    ),
                                }
                            ]
                        }
                    ]
                }
            ],
        }

        result = _transform_project(project)

        self.assertEqual(
            result["contacts"],
            [
                {
                    "name": "Projectteam Buikslotermeerplein",
                    "email": "buikslotermeerplein@amsterdam.nl",
                    "phone": None,
                    "position": None,
                    "extra": None,
                }
            ],
        )
        self.assertEqual(
            result["sections"]["contact"],
            [
                {
                    "body": (
                        '<div class="dds-prose"><p class="dds-paragraph">'
                        "Inloop voor vragen: elke laatste dinsdag van de maand "
                        "van 15.00 tot 17.00 uur, in InfoStek, "
                        "Buikslotermeerplein 13b</p></div>"
                    ),
                    "links": [],
                    "title": "Contact",
                }
            ],
        )

    def test_links_extraction_sections(self):
        project = {
            "id": 12,
            "title": "Buikslotermeerplein: stap voor stap levendiger en groener",
            "content": [
                {
                    "id": 86076,
                    "rows": [
                        {
                            "content": [
                                {
                                    "__typename": "ParagraphDdsLinkList",
                                    "id": 1,
                                    "contentIndication": "what",
                                    "content": '<div class="dds-prose"><p class="dds-paragraph">Het Buikslotermeerplein groeit stap voor stap uit tot een levendig hart van Noord. Met meer ruimte voor wonen, werken, groen, winkelen en uitgaan. We willen dat het Buikslotermeerplein een wijk wordt waar Noorderlingen trots op zijn, bewoners zich thuis voelen en Amsterdammers graag naar toe gaan. In de toekomst willen we de bouw van ongeveer 3000 woningen mogelijk maken. Deze plannen zijn gemaakt na gesprekken met buurtbewoners, ondernemers en andere belanghebbenden van het Buikslotermeerplein.</p><p class="dds-paragraph">Vanaf het begin spreken we met bewoners, ondernemers en andere betrokkenen over hun wensen en ideeën voor het gebied. Wilt u ook meedenken en meedoen?</p></div>',
                                    "items": [
                                        {
                                            "id": 2,
                                            "label": "Meedoen Buikslotermeerplein",
                                            "link": {
                                                "label": "Meedoen Buikslotermeerplein",
                                                "url": "https://dvo.amsterdam.nl/meedoen-buikslotermeerplein",
                                            },
                                        }
                                    ],
                                },
                            ]
                        },
                    ],
                }
            ],
        }

        result = _transform_project(project)

        self.assertEqual(
            result["sections"]["what"],
            [
                {
                    "body": '<div class="dds-prose"><p class="dds-paragraph">Het Buikslotermeerplein groeit stap voor stap uit tot een levendig hart van Noord. Met meer ruimte voor wonen, werken, groen, winkelen en uitgaan. We willen dat het Buikslotermeerplein een wijk wordt waar Noorderlingen trots op zijn, bewoners zich thuis voelen en Amsterdammers graag naar toe gaan. In de toekomst willen we de bouw van ongeveer 3000 woningen mogelijk maken. Deze plannen zijn gemaakt na gesprekken met buurtbewoners, ondernemers en andere belanghebbenden van het Buikslotermeerplein.</p><p class="dds-paragraph">Vanaf het begin spreken we met bewoners, ondernemers en andere betrokkenen over hun wensen en ideeën voor het gebied. Wilt u ook meedenken en meedoen?</p></div>',
                    "title": "Wat",
                    "links": [
                        {
                            "label": "Meedoen Buikslotermeerplein",
                            "url": "https://dvo.amsterdam.nl/meedoen-buikslotermeerplein",
                        }
                    ],
                }
            ],
        )

    def test_no_link_extraction_sections(self):
        project = {
            "id": 12,
            "title": "Buikslotermeerplein: stap voor stap levendiger en groener",
            "content": [
                {
                    "id": 86076,
                    "rows": [
                        {
                            "content": [
                                {
                                    "__typename": "ParagraphDdsRichText",
                                    "id": 4844,
                                    "contentIndication": "when",
                                    "content": '<div class="dds-prose"><h2 class="dds-heading dds-heading--2">Wanneer</h2><p class="dds-paragraph">In februari 2020 is het <a href="https://omgevingswet.overheid.nl/regels-op-de-kaart/documenten/NL-IMRO-0363-N1703BPGST-VG01-1/regels" class="dds-link">bestemmingsplan voor Elzenhagen Zuid</a> vastgesteld. We verwachten dat de ontwikkeling van Elzenhagen Zuid tot 2028 duurt.</p></div>',
                                },
                            ]
                        },
                    ],
                }
            ],
        }

        result = _transform_project(project)
        self.assertEqual(
            result["sections"]["when"],
            [
                {
                    "body": '<div class="dds-prose"><p class="dds-paragraph">In februari 2020 is het <a class="dds-link" href="https://omgevingswet.overheid.nl/regels-op-de-kaart/documenten/NL-IMRO-0363-N1703BPGST-VG01-1/regels">bestemmingsplan voor Elzenhagen Zuid</a> vastgesteld. We verwachten dat de ontwikkeling van Elzenhagen Zuid tot 2028 duurt.</p></div>',
                    "title": "Wanneer",
                    "links": [],
                }
            ],
        )
