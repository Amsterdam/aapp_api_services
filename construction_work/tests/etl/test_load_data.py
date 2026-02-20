from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker
from requests import HTTPError

from construction_work.etl.load_data import (
    articles,
    get_article_object,
    get_project_object,
    projects,
    store_image,
)
from construction_work.models.article_models import Article
from construction_work.models.project_models import (
    Project,
    ProjectImage,
    ProjectImageSource,
)


class LoadDataTestCase(TestCase):
    def _set_mock_image_set_service_side_effect(
        self, mock_image_set_service, image_data_list
    ):
        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = [
            {
                "id": image_data["id"],
                "variants": [
                    {
                        "image": x["uri"],
                        "width": x["width"],
                        "height": x["height"],
                    }
                    for x in image_data["sources"]
                ],
            }
            for image_data in image_data_list
        ]

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_projects(self, mock_image_set_service):
        """Test that projects function correctly creates or updates Project instances."""
        project_data = [
            {
                "id": 1,
                "title": "Project 1",
                "sections": {
                    "what": [
                        {
                            "body": "Het park Gaasperplas",
                            "links": [
                                {
                                    "url": "http://www.amsterdam.nl/",
                                    "label": "Bekijk wat we gaan doen",
                                }
                            ],
                            "title": None,
                        }
                    ],
                    "when": [],
                    "work": [],
                    "where": [{"body": "De Gaasperplas", "links": [], "title": "Waar"}],
                    "contact": [{"body": None, "links": [], "title": "Contact"}],
                },
                "contacts": [
                    {
                        "id": 1,
                        "name": "Jan",
                        "email": "jan@amsterdam.nl",
                        "phone": None,
                        "position": "Omgevingsmanager",
                    }
                ],
                "subtitle": "Subtitle 1",
                "timeline": {
                    "items": [
                        {
                            "body": "Cruquiusgebied verandere",
                            "items": [],
                            "title": "2008",
                            "collapsed": True,
                        },
                        {
                            "body": "Bouw woningen",
                            "items": [],
                            "title": "2011",
                            "collapsed": True,
                        },
                    ],
                    "title": "Wanneer",
                },
                "url": "http://example.com/project/1",
                "image": {
                    "id": 236,
                    "sources": [
                        {"uri": "https://image.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
            {
                "id": 2,
                "title": "Project 2",
                "subtitle": "Subtitle 2",
                "timeline": {
                    "items": [
                        {
                            "body": "Cruquiusgebied verandere",
                            "items": [],
                            "title": "2008",
                            "collapsed": True,
                        },
                        {
                            "body": "Bouw woningen",
                            "items": [],
                            "title": "2011",
                            "collapsed": True,
                        },
                    ],
                    "title": "Wanneer",
                },
                "image": {
                    "id": 238,
                    "sources": [
                        {"uri": "http://image2.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "url": "http://example.com/project/2",
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]
        self._set_mock_image_set_service_side_effect(
            mock_image_set_service, [p["image"] for p in project_data]
        )

        projects(project_data)

        self.assertEqual(Project.objects.count(), 2)
        project1 = Project.objects.get(foreign_id=1)
        project2 = Project.objects.get(foreign_id=2)

        self.assertEqual(project1.title, "Project 1")
        self.assertEqual(project2.title, "Project 2")

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_projects_no_sections(self, mock_image_set_service):
        """Test that projects function correctly creates or updates Project instances."""
        project_data = [
            {
                "id": 1,
                "title": "Project 1",
                "sections": {
                    "what": [],
                    "when": [],
                    "work": [],
                    "where": [],
                    "contact": [],
                },
                "contacts": [
                    {
                        "id": 1,
                        "name": "Jan",
                        "email": "jan@amsterdam.nl",
                        "phone": None,
                        "position": "Omgevingsmanager",
                    }
                ],
                "subtitle": "Subtitle 1",
                "timeline": {
                    "items": [
                        {
                            "body": "Cruquiusgebied verandere",
                            "items": [],
                            "title": "2008",
                            "collapsed": True,
                        },
                        {
                            "body": "Bouw woningen",
                            "items": [],
                            "title": "2011",
                            "collapsed": True,
                        },
                    ],
                    "title": "Wanneer",
                },
                "url": "http://example.com/project/1",
                "image": {
                    "id": 236,
                    "sources": [
                        {"uri": "https://image.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
            {
                "id": 2,
                "title": "Project 2",
                "subtitle": "Subtitle 2",
                "sections": {
                    "what": [
                        {
                            "body": "Het park Gaasperplas",
                            "links": [
                                {
                                    "url": "http://www.amsterdam.nl/",
                                    "label": "Bekijk wat we gaan doen",
                                }
                            ],
                            "title": None,
                        }
                    ],
                    "when": [],
                    "work": [],
                    "where": [{"body": "De Gaasperplas", "links": [], "title": "Waar"}],
                    "contact": [{"body": None, "links": [], "title": "Contact"}],
                },
                "timeline": {
                    "items": [
                        {
                            "body": "Cruquiusgebied verandere",
                            "items": [],
                            "title": "2008",
                            "collapsed": True,
                        },
                        {
                            "body": "Bouw woningen",
                            "items": [],
                            "title": "2011",
                            "collapsed": True,
                        },
                    ],
                    "title": "Wanneer",
                },
                "image": {
                    "id": 238,
                    "sources": [
                        {"uri": "http://image2.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "url": "http://example.com/project/2",
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]
        self._set_mock_image_set_service_side_effect(
            mock_image_set_service, [p["image"] for p in project_data]
        )

        projects(project_data)

        self.assertEqual(Project.objects.count(), 2)
        project1 = Project.objects.get(foreign_id=1)
        project2 = Project.objects.get(foreign_id=2)

        self.assertEqual(project1.active, False)
        self.assertEqual(project2.active, True)

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_projects_update_conflict(self, mock_image_set_service):
        """Test that projects function updates existing Project instances on conflict."""
        # Create an initial project
        initial_project = baker.make(Project, foreign_id=1)

        # New data with the same foreign_id
        project_data = [
            {
                "id": 1,
                "title": "Updated Title",
                "subtitle": "Updated Subtitle",
                "sections": {
                    "what": [
                        {
                            "body": "Het park Gaasperplas",
                            "links": [
                                {
                                    "url": "http://www.amsterdam.nl/",
                                    "label": "Bekijk wat we gaan doen",
                                }
                            ],
                            "title": None,
                        }
                    ],
                    "when": [],
                    "work": [],
                    "where": [{"body": "De Gaasperplas", "links": [], "title": "Waar"}],
                    "contact": [{"body": None, "links": [], "title": "Contact"}],
                },
                "timeline": {
                    "items": [
                        {
                            "body": "Cruquiusgebied verandere",
                            "items": [],
                            "title": "2008",
                            "collapsed": True,
                        },
                        {
                            "body": "Bouw woningen",
                            "items": [],
                            "title": "2011",
                            "collapsed": True,
                        },
                    ],
                    "title": "Wanneer",
                },
                "image": {
                    "id": 236,
                    "sources": [
                        {"uri": "https://image.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "url": "http://example.com/project/1",
                "coordinates": {"lat": 10, "lon": 20},
                "created": initial_project.creation_date,
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]
        self._set_mock_image_set_service_side_effect(
            mock_image_set_service, [p["image"] for p in project_data]
        )

        projects(project_data)

        # Fetch the project again to check updates
        updated_project = Project.objects.get(foreign_id=1)
        self.assertEqual(updated_project.title, "Updated Title")
        self.assertEqual(updated_project.subtitle, "Updated Subtitle")
        self.assertEqual(updated_project.sections.count(), 3)
        self.assertEqual(updated_project.timeline_items.count(), 2)
        self.assertEqual(updated_project.image.id, 236)
        self.assertEqual(updated_project.coordinates_lat, 10.0)
        self.assertEqual(updated_project.coordinates_lon, 20.0)

    def test_get_project_object(self):
        """Test that get_project_object creates a Project instance with correct attributes."""
        data = {
            "id": 1,
            "title": "Test Project",
            "subtitle": "A test project",
            "sections": {
                "what": [
                    {
                        "body": "Het park Gaasperplas",
                        "links": [
                            {
                                "url": "http://www.amsterdam.nl/",
                                "label": "Bekijk wat we gaan doen",
                            }
                        ],
                        "title": None,
                    }
                ],
                "when": [],
                "work": [],
                "where": [{"body": "De Gaasperplas", "links": [], "title": "Waar"}],
                "contact": [{"body": None, "links": [], "title": "Contact"}],
            },
            "contacts": [
                {
                    "id": 1,
                    "name": "Jan",
                    "email": "jan@amsterdam.nl",
                    "phone": None,
                    "position": "Omgevingsmanager",
                }
            ],
            "timeline": {
                "items": [
                    {
                        "body": "Cruquiusgebied verandere",
                        "items": [],
                        "title": "2008",
                        "collapsed": True,
                    },
                    {
                        "body": "Bouw woningen",
                        "items": [],
                        "title": "2011",
                        "collapsed": True,
                    },
                ],
                "title": "Wanneer",
            },
            "image": {
                "id": 236,
                "sources": [{"uri": "image.jpg", "width": 940, "height": 415}],
                "aspectRatio": 2,
            },
            "url": "http://example.com/project/1",
            "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
            "created": timezone.now(),
            "modified": timezone.now(),
            "publicationDate": timezone.now(),
            "expirationDate": None,
        }
        project = get_project_object(data)
        self.assertEqual(project.foreign_id, data["id"])
        self.assertEqual(project.title, data["title"])
        self.assertEqual(project.subtitle, data["subtitle"])
        self.assertEqual(project.url, data["url"])
        self.assertEqual(project.coordinates_lat, data["coordinates"]["lat"])
        self.assertEqual(project.coordinates_lon, data["coordinates"]["lon"])
        self.assertEqual(project.creation_date, data["created"])
        self.assertEqual(project.modification_date, data["modified"])
        self.assertEqual(project.publication_date, data["created"])
        self.assertEqual(project.expiration_date, data["expirationDate"])
        self.assertTrue(project.active)
        self.assertIsNotNone(project.last_seen)

    def test_articles(self):
        """Test that articles function correctly creates or updates Article instances and their relationships."""
        project1 = baker.make(Project, foreign_id=1)
        project2 = baker.make(Project, foreign_id=2)

        article_data = [
            {
                "id": 100,
                "title": "Article 1",
                "intro": "Intro 1",
                "body": "Body 1",
                "type": "announcement",
                "url": "http://example.com/article/100",
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
                "projectIds": [1, 2],
            },
            {
                "id": 101,
                "title": "Article 2",
                "intro": "Intro 2",
                "body": "Body 2",
                "type": "update",
                "url": "http://example.com/article/101",
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
                "projectIds": [1],
            },
        ]

        articles(article_data)

        self.assertEqual(Article.objects.count(), 2)
        article1 = Article.objects.get(foreign_id=100)
        article2 = Article.objects.get(foreign_id=101)

        self.assertEqual(article1.title, "Article 1")
        self.assertEqual(article2.title, "Article 2")

        # Check many-to-many relationships
        self.assertEqual(set(article1.projects.all()), {project1, project2})
        self.assertEqual(set(article2.projects.all()), {project1})

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_articles_update_conflict(self, mock_image_set_service):
        """Test that articles function updates existing Article instances on conflict."""
        article100 = baker.make(Article, id=100)
        project1 = baker.make(Project, foreign_id=1)

        # New data with the same foreign_id
        article_data = [
            {
                "id": 100,
                "title": "Updated Article Title",
                "intro": "Updated Intro",
                "body": "Updated Body",
                "type": "announcement",
                "url": "http://example.com/article/100",
                "created": article100.creation_date,
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
                "projectIds": [1],
                "image": {
                    "id": 23626572,
                    "sources": [
                        {"uri": "https://image.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
            },
        ]
        self._set_mock_image_set_service_side_effect(
            mock_image_set_service, [a["image"] for a in article_data]
        )

        articles(article_data)

        # Fetch the article again to check updates
        updated_article = Article.objects.get(foreign_id=100)
        self.assertEqual(updated_article.title, "Updated Article Title")
        self.assertEqual(updated_article.intro, "Updated Intro")
        self.assertEqual(updated_article.body, "Updated Body")
        self.assertEqual(updated_article.image.id, 23626572)
        self.assertEqual(updated_article.type, "announcement")
        self.assertEqual(set(updated_article.projects.all()), {project1})

    def test_articles_missing_project(self):
        """Test that articles function logs an error when a referenced project does not exist."""
        article_data = [
            {
                "id": 200,
                "title": "Article with Missing Project",
                "intro": "Intro",
                "body": "Body",
                "type": "news",
                "url": "http://example.com/article/200",
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
                "projectIds": [999],  # Non-existent project ID
            },
        ]

        with self.assertLogs("construction_work.etl.load_data", level="ERROR") as cm:
            articles(article_data)

        self.assertIn("Project ID 999 not found in database", cm.output[0])
        article = Article.objects.get(foreign_id=200)
        self.assertEqual(article.projects.count(), 0)

    def test_get_article_object(self):
        """Test that get_article_object creates an Article instance with correct attributes."""
        data = {
            "id": 100,
            "title": "Article Title",
            "intro": "Article Intro",
            "body": "Article Body",
            "type": "news",
            "url": "http://example.com/article/100",
            "created": timezone.now(),
            "modified": timezone.now(),
            "publicationDate": timezone.now(),
            "expirationDate": None,
            "image": {
                "id": 23626572,
                "sources": [{"uri": "image.jpg", "width": 940, "height": 415}],
                "aspectRatio": 2,
            },
        }
        article = get_article_object(data)
        self.assertEqual(article.foreign_id, data["id"])
        self.assertEqual(article.title, data["title"])
        self.assertEqual(article.intro, data["intro"])
        self.assertEqual(article.body, data["body"])
        self.assertEqual(article.type, data["type"])
        self.assertEqual(article.url, data["url"])
        self.assertEqual(article.creation_date, data["created"])
        self.assertEqual(article.modification_date, data["modified"])
        self.assertEqual(article.publication_date, data["created"])
        self.assertEqual(article.expiration_date, data["expirationDate"])

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_store_image_expected_source_data(self, mock_image_set_service):
        parent = baker.make(Project, foreign_id=1)
        image_class = ProjectImage
        image_source_class = ProjectImageSource

        project_data = {
            "image": {
                "id": 100,
                "sources": [
                    {
                        "uri": "https://foo.bar/medium-image.jpg",
                        "width": 200,
                        "height": 20,
                    },
                    {
                        "uri": "https://foo.bar/big-image.jpg",
                        "width": 20,
                        "height": 201,
                    },
                    {
                        "uri": "https://foo.bar/small-image.jpg",
                        "width": 19,
                        "height": 200,
                    },
                ],
                "aspectRatio": 2,
            }
        }

        self._set_mock_image_set_service_side_effect(
            mock_image_set_service, [project_data["image"]]
        )

        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )

        self.assertEqual(len(images), 1)
        self.assertEqual(len(sources), 3)
        self.assertIsNotNone(images[0].image_set)

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_store_image_width_height_as_strings(self, mock_image_set_service):
        parent = baker.make(Project, foreign_id=1)
        image_class = ProjectImage
        image_source_class = ProjectImageSource

        project_data = {
            "image": {
                "id": 100,
                "sources": [
                    {
                        "uri": "https://foo.bar/medium-image.jpg",
                        "width": "200",
                        "height": "20",
                    },
                    {
                        "uri": "https://foo.bar/big-image.jpg",
                        "width": "20",
                        "height": "201",
                    },
                    {
                        "uri": "https://foo.bar/small-image.jpg",
                        "width": 19,
                        "height": 200,
                    },
                ],
                "aspectRatio": 2,
            }
        }

        self._set_mock_image_set_service_side_effect(
            mock_image_set_service, [project_data["image"]]
        )

        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )

        self.assertEqual(len(images), 1)
        self.assertEqual(len(sources), 3)
        self.assertIsNotNone(images[0].image_set)

    def test_store_image_invalid_source_data(self):
        parent = baker.make(Project, foreign_id=1)
        image_class = ProjectImage
        image_source_class = ProjectImageSource

        # Missing width and height
        project_data = {
            "image": {"id": 100, "sources": [{"uri": "https://foo.bar/image.jpg"}]}
        }
        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )
        self.assertEqual(len(images), 0)
        self.assertEqual(len(sources), 0)

        # Width or height not integer
        project_data = {
            "image": {
                "id": 100,
                "sources": [
                    {
                        "uri": "https://foo.bar/image.jpg",
                        "width": "not an integer",
                        "height": 200,
                    }
                ],
            }
        }
        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )
        self.assertEqual(len(images), 0)
        self.assertEqual(len(sources), 0)

    def test_store_image_no_sources(self):
        parent = baker.make(Project, foreign_id=1)
        image_class = ProjectImage
        image_source_class = ProjectImageSource

        project_data = {"image": {"id": 100, "sources": []}}
        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )
        self.assertEqual(len(images), 0)
        self.assertEqual(len(sources), 0)

    def test_store_image_missing_source_uri(self):
        parent = baker.make(Project, foreign_id=1)
        image_class = ProjectImage
        image_source_class = ProjectImageSource

        project_data = {
            "image": {"id": 100, "sources": [{"width": 100, "height": 100}]}
        }
        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )
        self.assertEqual(len(images), 0)
        self.assertEqual(len(sources), 0)

    @patch("construction_work.etl.load_data.ImageSetService")
    def test_store_image_http_error(self, mock_image_set_service):
        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = (
            HTTPError("Something went wrong")
        )
        parent = baker.make(Project, foreign_id=1)
        image_class = ProjectImage
        image_source_class = ProjectImageSource

        project_data = {
            "image": {
                "id": 100,
                "sources": [
                    {"uri": "https://foo.bar/image.jpg", "width": 100, "height": 100}
                ],
            }
        }
        images, sources = store_image(
            project_data, parent, image_class, image_source_class
        )
        self.assertEqual(len(images), 0)
        self.assertEqual(len(sources), 0)
