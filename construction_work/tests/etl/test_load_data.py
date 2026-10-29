from unittest import mock

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from construction_work.etl import load_data as load_data_module
from construction_work.etl.load_data import (
    get_article_object,
    get_project_object,
    get_sections,
    load_articles,
    load_projects,
    store_image,
)
from construction_work.models.article_models import Article, ArticleImage
from construction_work.models.project_models import (
    Project,
    ProjectContact,
    ProjectImage,
)


class LoadDataTestCase(TestCase):
    def test_load_data_dispatches_empty_defaults(self):
        with (
            mock.patch.object(load_data_module, "load_projects") as load_projects,
            mock.patch.object(load_data_module, "load_articles") as load_articles,
        ):
            load_data_module.load_data({})

        load_projects.assert_called_once_with([])
        load_articles.assert_called_once_with([])

    def test_get_sections_without_sections(self):
        self.assertEqual(get_sections({}, None), ([], []))

    def test_projects(self):
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
                "imageSet": {
                    "id": 236,
                    "variants": [
                        {"image": "https://image.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
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
                "contacts": [
                    {
                        "name": "Wendy",
                        "email": "wendy@amsterdam.nl",
                        "phone": None,
                        "position": "Omgevingsmanager",
                    }
                ],
            },
        ]
        load_projects(project_data)

        self.assertEqual(Project.objects.count(), 2)
        project1 = Project.objects.get(drupal_id=1)
        project2 = Project.objects.get(drupal_id=2)

        self.assertEqual(project1.title, "Project 1")
        self.assertEqual(project2.title, "Project 2")
        self.assertEqual(
            ProjectContact.objects.get(name="Wendy").project.drupal_id,
            2,
        )

    def test_multiple_contacts_receive_generated_primary_keys(self):
        load_projects(
            [
                {
                    "id": 3,
                    "title": "Project with multiple contacts",
                    "url": "https://example.com/project/3",
                    "creation_date": timezone.now(),
                    "modification_date": timezone.now(),
                    "publication_date": timezone.now(),
                    "contacts": [
                        {"name": "First contact"},
                        {"name": "Second contact"},
                        {"name": "Third contact"},
                    ],
                }
            ]
        )

        contacts = list(ProjectContact.objects.order_by("id"))

        self.assertEqual(len(contacts), 3)
        self.assertEqual(
            [contact.name for contact in contacts],
            ["First contact", "Second contact", "Third contact"],
        )
        self.assertEqual(len({contact.pk for contact in contacts}), 3)

    def test_projects_no_sections(self):
        """
        Test that without filled sections are deactivated and those
        with filled sections remain active
        """
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
                "image_set": {
                    "id": 236,
                    "variants": [
                        {
                            "uri": "https://image.jpg",
                            "width": 940,
                            "height": 415,
                        }
                    ],
                },
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
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
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
            },
            {
                "id": 3,
                "title": "Project 3",
                "subtitle": "Subtitle 3",
                "timeline": {
                    "items": [
                        {
                            "body": "Cruquiusgebied verandere",
                            "items": [],
                            "title": "2008",
                            "collapsed": True,
                        }
                    ],
                    "title": "Wanneer",
                },
                "image": {
                    "id": 240,
                    "sources": [
                        {"uri": "http://image3.jpg", "width": 940, "height": 415}
                    ],
                    "aspectRatio": 2,
                },
                "url": "http://example.com/project/3",
                "coordinates": {"lat": 52.3077814027491, "lon": 4.99128045578052},
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]
        load_projects(project_data)

        self.assertEqual(Project.objects.count(), 3)
        project1 = Project.objects.get(drupal_id=1)
        project2 = Project.objects.get(drupal_id=2)
        project3 = Project.objects.get(drupal_id=3)

        self.assertEqual(project1.active, False)
        self.assertEqual(project2.active, True)
        self.assertEqual(project3.active, False)

    def test_projects_update_conflict(self):
        """Test that projects function updates existing Project instances on conflict."""
        # Create an initial project
        initial_project = baker.make(Project, foreign_id=51, drupal_id=1)

        # New data with the same Drupal ID
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
                "image_set": {
                    "id": 236,
                    "variants": [
                        {
                            "uri": "https://image.jpg",
                            "width": 940,
                            "height": 415,
                        }
                    ],
                },
                "url": "http://example.com/project/1",
                "coordinates": {"lat": 10, "lon": 20},
                "created": initial_project.creation_date,
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]
        load_projects(project_data)

        # Fetch the project again to check updates
        updated_project = Project.objects.get(drupal_id=1)
        self.assertEqual(updated_project.foreign_id, 51)
        self.assertEqual(updated_project.title, "Updated Title")
        self.assertEqual(updated_project.subtitle, "Updated Subtitle")
        self.assertEqual(updated_project.sections.count(), 3)
        self.assertEqual(updated_project.timeline_items.count(), 2)
        self.assertTrue(
            ProjectImage.objects.filter(
                project=updated_project, foreign_id=236
            ).exists()
        )
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
            "creation_date": timezone.now(),
            "modification_date": timezone.now(),
            "publication_date": timezone.now(),
            "expiration_date": None,
        }
        project = get_project_object(data)
        self.assertEqual(project.drupal_id, data["id"])
        self.assertIsNone(project.foreign_id)
        self.assertEqual(project.title, data["title"])
        self.assertEqual(project.subtitle, data["subtitle"])
        self.assertEqual(project.url, data["url"])
        self.assertEqual(project.coordinates_lat, data["coordinates"]["lat"])
        self.assertEqual(project.coordinates_lon, data["coordinates"]["lon"])
        self.assertEqual(project.creation_date, data["creation_date"])
        self.assertEqual(project.modification_date, data["modification_date"])
        self.assertEqual(project.publication_date, data["publication_date"])
        self.assertEqual(project.expiration_date, data["expiration_date"])
        self.assertTrue(project.active)
        self.assertIsNotNone(project.last_seen)

    def test_articles(self):
        """Test that articles function correctly creates or updates Article instances and their relationships."""
        project1 = baker.make(Project, foreign_id=1, drupal_id=1)
        project2 = baker.make(Project, foreign_id=2, drupal_id=2)

        article_data = [
            {
                "id": 100,
                "title": "Article 1",
                "intro": "Intro 1",
                "body": "Body 1",
                "type": "announcement",
                "url": "http://example.com/article/100",
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
                "projectIds": [1, 2],
            },
            {
                "id": 101,
                "title": "Article 2",
                "intro": "Intro 2",
                "body": "Body 2",
                "type": "update",
                "url": "http://example.com/article/101",
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
                "projectIds": [1],
            },
        ]

        load_articles(article_data)

        self.assertEqual(Article.objects.count(), 2)
        article1 = Article.objects.get(drupal_id=100)
        article2 = Article.objects.get(drupal_id=101)

        self.assertEqual(article1.title, "Article 1")
        self.assertEqual(article2.title, "Article 2")

        # Check many-to-many relationships
        self.assertEqual(set(article1.projects.all()), {project1, project2})
        self.assertEqual(set(article2.projects.all()), {project1})

    def test_articles_update_conflict(self):
        """Test that articles function updates existing Article instances on conflict."""
        article100 = baker.make(Article, id=100, drupal_id=100, foreign_id=500)
        project1 = baker.make(Project, foreign_id=1, drupal_id=1)

        # New data with the same Drupal ID
        article_data = [
            {
                "id": 100,
                "title": "Updated Article Title",
                "intro": "Updated Intro",
                "body": "Updated Body",
                "type": "announcement",
                "url": "http://example.com/article/100",
                "creation_date": article100.creation_date,
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
                "projectIds": [1],
                "image_set": {
                    "id": 23626572,
                    "variants": [
                        {
                            "uri": "https://image.jpg",
                            "width": 940,
                            "height": 415,
                        }
                    ],
                },
            },
        ]

        load_articles(article_data)

        # Fetch the article again to check updates
        updated_article = Article.objects.get(drupal_id=100)
        self.assertEqual(updated_article.foreign_id, 500)
        self.assertEqual(updated_article.title, "Updated Article Title")
        self.assertEqual(updated_article.intro, "Updated Intro")
        self.assertEqual(updated_article.body, "Updated Body")
        self.assertEqual(
            ArticleImage.objects.get(article=updated_article).foreign_id, 23626572
        )
        self.assertEqual(updated_article.type, "announcement")
        self.assertEqual(set(updated_article.projects.all()), {project1})

    def test_articles_load_with_nullable_legacy_id(self):
        project = baker.make(Project, foreign_id=None, drupal_id=1)
        article_data = [
            {
                "id": 100,
                "title": "Article without legacy ID",
                "intro": "Intro",
                "body": "Body",
                "type": "news",
                "url": "http://example.com/article/100",
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
                "projectIds": [1],
            }
        ]

        load_articles(article_data)

        article = Article.objects.get(drupal_id=100)
        self.assertIsNone(article.foreign_id)
        self.assertEqual(list(article.projects.all()), [project])

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
                "creation_date": timezone.now(),
                "modification_date": timezone.now(),
                "publication_date": timezone.now(),
                "expiration_date": None,
                "projectIds": [999],  # Non-existent project ID
            },
        ]

        with self.assertLogs("construction_work.etl.load_data", level="ERROR") as cm:
            load_articles(article_data)

        self.assertIn("Project ID 999 not found in database", cm.output[0])
        article = Article.objects.get(drupal_id=200)
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
            "creation_date": timezone.now(),
            "modification_date": timezone.now(),
            "publication_date": timezone.now(),
            "expiration_date": None,
            "image": {
                "id": 23626572,
                "sources": [{"uri": "image.jpg", "width": 940, "height": 415}],
                "aspectRatio": 2,
            },
        }
        article = get_article_object(data)
        self.assertEqual(article.drupal_id, data["id"])
        self.assertIsNone(article.foreign_id)
        self.assertEqual(article.title, data["title"])
        self.assertEqual(article.intro, data["intro"])
        self.assertEqual(article.body, data["body"])
        self.assertEqual(article.type, data["type"])
        self.assertEqual(article.url, data["url"])
        self.assertEqual(article.creation_date, data["creation_date"])
        self.assertEqual(article.modification_date, data["modification_date"])
        self.assertEqual(article.publication_date, data["publication_date"])
        self.assertEqual(article.expiration_date, data["expiration_date"])

    def test_store_image_creates_one_row_per_variant(self):
        project = baker.make(Project, foreign_id=1)
        image_data = {
            "image_set": {
                "id": 100,
                "variants": [
                    {
                        "uri": "https://foo.bar/medium-image.jpg",
                        "width": "200",
                        "height": "20",
                    },
                    {
                        "uri": "https://foo.bar/big-image.jpg",
                        "width": 20,
                        "height": 201,
                    },
                ],
                "aspectRatio": 2,
                "alternativeText": "Project image",
            }
        }

        images = store_image(image_data, project, ProjectImage, "project")

        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].foreign_id, 100)
        self.assertEqual(images[0].uri, "https://foo.bar/medium-image.jpg")
        self.assertEqual(images[0].width, 200)
        self.assertEqual(images[0].height, 20)
        ProjectImage.objects.bulk_create(images)
        self.assertEqual(project.images.count(), 2)
        self.assertEqual(images[1].foreign_id, 100)

    def test_store_image_rejects_invalid_variant_data(self):
        project = baker.make(Project, foreign_id=1)
        image_data = {
            "image_set": {
                "id": 100,
                "variants": [
                    {
                        "uri": "https://foo.bar/image.jpg",
                        "width": "not an integer",
                        "height": 100,
                    }
                ],
            }
        }

        with self.assertLogs("construction_work.etl.load_data", level="ERROR"):
            self.assertEqual(
                store_image(image_data, project, ProjectImage, "project"),
                [],
            )

    def test_store_image_without_variants_returns_empty_list(self):
        project = baker.make(Project, foreign_id=1)
        self.assertEqual(
            store_image(
                {"image_set": {"id": 100, "variants": []}},
                project,
                ProjectImage,
                "project",
            ),
            [],
        )

    def test_store_image_without_uri_returns_empty_list(self):
        project = baker.make(Project, foreign_id=1)
        image_data = {
            "image_set": {
                "id": 100,
                "variants": [
                    {
                        "image": "https://example.invalid/image.jpg",
                        "width": 20,
                        "height": 10,
                    }
                ],
            }
        }

        with self.assertLogs("construction_work.etl.load_data", level="ERROR"):
            images = store_image(image_data, project, ProjectImage, "project")

        self.assertEqual(images, [])
