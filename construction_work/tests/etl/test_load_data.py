from django.test import TestCase
from django.utils import timezone

from construction_work.etl.load_data import (
    articles,
    get_article_object,
    get_project_object,
    projects,
)
from construction_work.models import Article, Project


class LoadDataTestCase(TestCase):
    def test_projects(self):
        """Test that projects function correctly creates or updates Project instances."""
        project_data = [
            {
                "id": 1,
                "title": "Project 1",
                "subtitle": "Subtitle 1",
                "sections": ["Section A"],
                "contacts": ["Contact A"],
                "timeline": ["2021-01-01", "2021-06-30"],
                "image": "image_url_1",
                "images": ["image1_url"],
                "url": "http://example.com/project/1",
                "coordinates": [10.0, 20.0],
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
            {
                "id": 2,
                "title": "Project 2",
                "subtitle": "Subtitle 2",
                "sections": ["Section B"],
                "contacts": ["Contact B"],
                "timeline": ["2021-07-01", "2021-12-31"],
                "image": "image_url_2",
                "images": ["image2_url"],
                "url": "http://example.com/project/2",
                "coordinates": [30.0, 40.0],
                "created": timezone.now(),
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]
        projects(project_data)

        self.assertEqual(Project.objects.count(), 2)
        project1 = Project.objects.get(foreign_id=1)
        project2 = Project.objects.get(foreign_id=2)

        self.assertEqual(project1.title, "Project 1")
        self.assertEqual(project2.title, "Project 2")

    def test_projects_update_conflict(self):
        """Test that projects function updates existing Project instances on conflict."""
        # Create an initial project
        initial_project = Project.objects.create(
            foreign_id=1,
            title="Initial Title",
            subtitle="Initial Subtitle",
            sections=["Initial Section"],
            contacts=["Initial Contact"],
            timeline=["2020-01-01", "2020-12-31"],
            image="initial_image_url",
            images=["initial_image1_url"],
            url="http://example.com/project/1",
            coordinates=[0.0, 0.0],
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            publication_date=timezone.now(),
            expiration_date=None,
            last_seen=timezone.now(),
            active=True,
        )

        # New data with the same foreign_id
        project_data = [
            {
                "id": 1,
                "title": "Updated Title",
                "subtitle": "Updated Subtitle",
                "sections": ["Updated Section"],
                "contacts": ["Updated Contact"],
                "timeline": ["2021-01-01", "2021-12-31"],
                "image": "updated_image_url",
                "images": ["updated_image1_url"],
                "url": "http://example.com/project/1",
                "coordinates": [10.0, 20.0],
                "created": initial_project.creation_date,
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
            },
        ]

        projects(project_data)

        # Fetch the project again to check updates
        updated_project = Project.objects.get(foreign_id=1)
        self.assertEqual(updated_project.title, "Updated Title")
        self.assertEqual(updated_project.subtitle, "Updated Subtitle")
        self.assertEqual(updated_project.sections, ["Updated Section"])
        self.assertEqual(updated_project.contacts, ["Updated Contact"])
        self.assertEqual(updated_project.timeline, ["2021-01-01", "2021-12-31"])
        self.assertEqual(updated_project.image, "updated_image_url")
        self.assertEqual(updated_project.images, ["updated_image1_url"])
        self.assertEqual(updated_project.coordinates, [10.0, 20.0])

    def test_get_project_object(self):
        """Test that get_project_object creates a Project instance with correct attributes."""
        data = {
            "id": 1,
            "title": "Test Project",
            "subtitle": "A test project",
            "sections": ["Section 1", "Section 2"],
            "contacts": ["Contact 1"],
            "timeline": ["2021-01-01", "2021-12-31"],
            "image": "image_url",
            "images": ["image1_url", "image2_url"],
            "url": "http://example.com/project/1",
            "coordinates": [12.34, 56.78],
            "created": timezone.now(),
            "modified": timezone.now(),
            "publicationDate": timezone.now(),
            "expirationDate": None,
        }
        project = get_project_object(data)
        self.assertEqual(project.foreign_id, data["id"])
        self.assertEqual(project.title, data["title"])
        self.assertEqual(project.subtitle, data["subtitle"])
        self.assertEqual(project.sections, data["sections"])
        self.assertEqual(project.contacts, data["contacts"])
        self.assertEqual(project.timeline, data["timeline"])
        self.assertEqual(project.image, data["image"])
        self.assertEqual(project.images, data["images"])
        self.assertEqual(project.url, data["url"])
        self.assertEqual(project.coordinates, data["coordinates"])
        self.assertEqual(project.creation_date, data["created"])
        self.assertEqual(project.modification_date, data["modified"])
        self.assertEqual(project.publication_date, data["publicationDate"])
        self.assertEqual(project.expiration_date, data["expirationDate"])
        self.assertTrue(project.active)
        self.assertIsNotNone(project.last_seen)

    def test_articles(self):
        """Test that articles function correctly creates or updates Article instances and their relationships."""
        project1 = Project.objects.create(
            foreign_id=1,
            title="Project 1",
            subtitle="Subtitle 1",
            sections=["Section A"],
            contacts=["Contact A"],
            timeline=["2021-01-01", "2021-06-30"],
            image="image_url_1",
            images=["image1_url"],
            url="http://example.com/project/1",
            coordinates=[10.0, 20.0],
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            publication_date=timezone.now(),
            expiration_date=None,
            last_seen=timezone.now(),
            active=True,
        )

        project2 = Project.objects.create(
            foreign_id=2,
            title="Project 2",
            subtitle="Subtitle 2",
            sections=["Section B"],
            contacts=["Contact B"],
            timeline=["2021-07-01", "2021-12-31"],
            image="image_url_2",
            images=["image2_url"],
            url="http://example.com/project/2",
            coordinates=[30.0, 40.0],
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            publication_date=timezone.now(),
            expiration_date=None,
            last_seen=timezone.now(),
            active=True,
        )

        article_data = [
            {
                "id": 100,
                "title": "Article 1",
                "intro": "Intro 1",
                "body": "Body 1",
                "image": "article_image_url_1",
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
                "image": "article_image_url_2",
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

    def test_articles_update_conflict(self):
        """Test that articles function updates existing Article instances on conflict."""
        # Create an initial article
        initial_article = Article.objects.create(
            foreign_id=100,
            title="Initial Article Title",
            intro="Initial Intro",
            body="Initial Body",
            image="initial_article_image_url",
            type="news",
            url="http://example.com/article/100",
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            publication_date=timezone.now(),
            expiration_date=None,
        )

        # Create projects
        project1 = Project.objects.create(
            foreign_id=1,
            title="Project 1",
            subtitle="Subtitle 1",
            sections=["Section A"],
            contacts=["Contact A"],
            timeline=["2021-01-01", "2021-06-30"],
            image="image_url_1",
            images=["image1_url"],
            url="http://example.com/project/1",
            coordinates=[10.0, 20.0],
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            publication_date=timezone.now(),
            expiration_date=None,
            last_seen=timezone.now(),
            active=True,
        )

        # New data with the same foreign_id
        article_data = [
            {
                "id": 100,
                "title": "Updated Article Title",
                "intro": "Updated Intro",
                "body": "Updated Body",
                "image": "updated_article_image_url",
                "type": "announcement",
                "url": "http://example.com/article/100",
                "created": initial_article.creation_date,
                "modified": timezone.now(),
                "publicationDate": timezone.now(),
                "expirationDate": None,
                "projectIds": [1],
            },
        ]

        articles(article_data)

        # Fetch the article again to check updates
        updated_article = Article.objects.get(foreign_id=100)
        self.assertEqual(updated_article.title, "Updated Article Title")
        self.assertEqual(updated_article.intro, "Updated Intro")
        self.assertEqual(updated_article.body, "Updated Body")
        self.assertEqual(updated_article.image, "updated_article_image_url")
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
                "image": "image_url",
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
            "image": "article_image_url",
            "type": "news",
            "url": "http://example.com/article/100",
            "created": timezone.now(),
            "modified": timezone.now(),
            "publicationDate": timezone.now(),
            "expirationDate": None,
        }
        article = get_article_object(data)
        self.assertEqual(article.foreign_id, data["id"])
        self.assertEqual(article.title, data["title"])
        self.assertEqual(article.intro, data["intro"])
        self.assertEqual(article.body, data["body"])
        self.assertEqual(article.image, data["image"])
        self.assertEqual(article.type, data["type"])
        self.assertEqual(article.url, data["url"])
        self.assertEqual(article.creation_date, data["created"])
        self.assertEqual(article.modification_date, data["modified"])
        self.assertEqual(article.publication_date, data["publicationDate"])
        self.assertEqual(article.expiration_date, data["expirationDate"])
