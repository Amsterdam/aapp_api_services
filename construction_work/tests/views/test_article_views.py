import json
from datetime import datetime
from os.path import join

from django.urls import reverse
from model_bakery import baker

from construction_work.models.article_models import (
    Article,
    ArticleImage,
    ArticleImageSource,
)
from construction_work.models.manage_models import Image, WarningImage, WarningMessage
from construction_work.models.project_models import Project
from construction_work.tests import mock_data
from construction_work.tests.views.test_project_views import (
    ROOT_DIR,
    BaseTestProjectView,
)
from construction_work.utils.date_utils import translate_timezone as tt
from construction_work.utils.patch_utils import create_image_file
from core.tests.test_authentication import BasicAPITestCase


class TestArticleDetailView(BasicAPITestCase):
    def setUp(self):
        """Setup test db"""
        super().setUp()
        self.api_url = reverse("construction-work:get-article")

        projects = []
        for project_data in mock_data.projects:
            project = Project.objects.create(**project_data)
            projects.append(project)

        articles = []
        for article_data in mock_data.articles:
            article = Article.objects.create(**article_data)
            articles.append(article)

        articles[0].projects.add(projects[0])
        articles[0].publication_date = "2023-01-01T12:00:00+00:00"
        articles[0].save()

        articles[1].projects.add(projects[1])
        articles[1].publication_date = "2023-01-01T11:00:00+00:00"
        articles[1].save()

        baker.make(ArticleImage, id=1, parent=articles[0])

    def test_get_single_article(self):
        """Test retrieving single article"""
        article = Article.objects.first()
        result = self.client.get(
            self.api_url, {"id": article.pk}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        target_tzinfo_creation = datetime.fromisoformat(
            result.data["creation_date"]
        ).tzinfo
        target_tzinfo_last_seen = datetime.fromisoformat(
            result.data["last_seen"]
        ).tzinfo

        expected_data = {
            "id": article.pk,
            "meta_id": {
                "id": article.pk,
                "type": "article",
            },
            "foreign_id": article.foreign_id,
            "active": article.active,
            "last_seen": tt(str(article.last_seen), target_tzinfo_last_seen),
            "title": article.title,
            "intro": article.intro,
            "body": article.body,
            "image": {
                "id": article.image.id,
                "aspectRatio": article.image.aspectRatio,
                "alternativeText": article.image.alternativeText,
                "sources": [],
            },
            "url": article.url,
            "creation_date": tt(str(article.creation_date), target_tzinfo_creation),
            "modification_date": tt(
                str(article.modification_date), target_tzinfo_creation
            ),
            "publication_date": tt(
                str(article.publication_date), target_tzinfo_creation
            ),
            "expiration_date": tt(str(article.expiration_date), target_tzinfo_creation),
            "projects": [x.pk for x in article.projects.all()],
        }
        result_dict = json.loads(result.content)
        self.assertDictEqual(result_dict, expected_data)

    def test_missing_article_id(self):
        """Test calling API without article id param"""
        result = self.client.get(
            self.api_url, {"foobar": "foobar"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_article_not_found(self):
        """Test requesting article id which does not exist"""
        result = self.client.get(self.api_url, {"id": 9999}, headers=self.api_headers)
        self.assertEqual(result.status_code, 404)


class TestArticleListView(BaseTestProjectView):
    """Test multiple articles view"""

    def setUp(self):
        """Setup test db"""
        super().setUp()
        self.api_url = reverse("construction-work:article-list")

        projects = []
        for project_data in mock_data.projects:
            project = Project.objects.create(**project_data)
            projects.append(project)

        articles = []
        for article_data in mock_data.articles:
            article = Article.objects.create(**article_data)
            articles.append(article)

        articles[0].projects.add(projects[0])
        articles[0].publication_date = "2023-01-01T12:00:00+00:00"
        articles[0].save()

        articles[1].projects.add(projects[1])
        articles[1].publication_date = "2023-01-01T11:00:00+00:00"
        articles[1].save()

        warning_data = mock_data.warning_message.copy()
        warning_data["project_id"] = projects[0].pk
        warning = WarningMessage.objects.create(**warning_data)
        warning.publication_date = "2023-01-01T10:00:00+00:00"
        warning.save()

    def test_get_all(self):
        """Test get all news"""
        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 3)

    def test_get_limit_one(self):
        """Test limiting the result to one article"""
        result = self.client.get(self.api_url, {"limit": 1}, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 1)

    def test_invalid_limit(self):
        """Test passing invalid limit char"""
        result = self.client.get(
            self.api_url, {"limit": "1.1"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_get_articles_of_single_project(self):
        """Test get news from a single project"""
        first_project = Project.objects.first()

        result = self.client.get(
            self.api_url, {"project_ids": first_project.pk}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 2)

    def test_get_articles_of_multiple_projects(self):
        """Test get news from multiple projects"""
        first_project = Project.objects.first()
        last_project = Project.objects.last()

        result = self.client.get(
            self.api_url,
            {"project_ids": f"{first_project.pk},{last_project.pk}"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 3)

    def test_invalid_project_id(self):
        """Test passing invalid project id in comma seperated list"""
        result = self.client.get(
            self.api_url, {"project_ids": "1,foobar"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_article_content(self):
        """Test if content of article is as expected"""
        result = self.client.get(
            self.api_url,
            {"sort_by": "publication_date", "sort_order": "desc"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        article = Article.objects.order_by("-publication_date").first()

        expected_data = {
            "title": article.title,
            "publication_date": article.publication_date,
            "meta_id": {
                "type": "article",
                "id": article.pk,
            },
            "images": [],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_article_content_with_image(self):
        """Test if content of article with image is as expected"""
        image_data = {
            "id": 123,
            "sources": [
                {
                    "uri": "/foo/bar.png",
                    "width": 100,
                    "height": 50,
                },
            ],
            "aspectRatio": 2.0,
            "alternativeText": None,
        }

        article_data = mock_data.articles[0].copy()
        article_data["foreign_id"] = 9999
        article = Article.objects.create(**article_data)
        image = baker.make(
            ArticleImage, parent=article, alternativeText=None, aspectRatio=2.0, id=123
        )
        baker.make(
            ArticleImageSource, image=image, height=50, uri="/foo/bar.png", width=100
        )

        # Refresh from db to create datetime objects from datetime strings
        article.refresh_from_db()

        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 9999
        project = Project.objects.create(**project_data)

        article.projects.add(project)

        result = self.client.get(
            self.api_url, {"project_ids": [project.pk]}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        expected_data = {
            "title": article.title,
            "publication_date": article.publication_date,
            "meta_id": {
                "type": "article",
                "id": article.pk,
            },
            "images": [image_data],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_warning_content(self):
        """Test if content of warning is as expected"""
        result = self.client.get(
            self.api_url,
            {"sort_by": "publication_date", "sort_order": "asc"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        warning = WarningMessage.objects.first()

        expected_data = {
            # "type": "warning",
            "title": warning.title,
            "publication_date": warning.publication_date,
            "meta_id": {
                "type": "warning",
                "id": warning.pk,
            },
            "images": [],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_warning_content_with_image(self):
        """Test if content of warning with image is as expected"""
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 9999
        project = Project.objects.create(**project_data)

        warning_data = mock_data.warning_message.copy()
        warning_data["project_id"] = project.pk
        warning = WarningMessage.objects.create(**warning_data)
        warning.refresh_from_db()

        warning_image_data = {
            "warning_id": warning.pk,
        }
        warning_image = WarningImage.objects.create(**warning_image_data)

        image_data = mock_data.images[0].copy()
        image_data["image"] = create_image_file(
            join(ROOT_DIR, "construction_work/tests/image_data/small_image.png")
        )
        image = Image.objects.create(**image_data)
        warning_image.images.add(image)

        result = self.client.get(
            self.api_url, {"project_ids": project.pk}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        expected_data = {
            "title": warning.title,
            "publication_date": warning.publication_date,
            "meta_id": {
                "type": "warning",
                "id": warning.pk,
            },
            "images": [
                {
                    "id": warning_image.pk,
                    "sources": [
                        {
                            "uri": "http://testserver/construction-work/media/construction-work/images/image.jpg",
                            "width": image.width,
                            "height": image.height,
                        }
                    ],
                }
            ],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_sort_news_by_publication_date_descending(self):
        """Test getting news sorted by publication date descending"""
        articles = Article.objects.all()
        warnings = WarningMessage.objects.all()
        news = []
        news.extend(articles)
        news.extend(warnings)
        news_pub_dates = [x.publication_date for x in news]
        sorted_pub_dates = sorted(news_pub_dates, reverse=True)

        result = self.client.get(
            self.api_url,
            {"sort_by": "publication_date", "sort_order": "desc"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        result_pub_dates = [x["publication_date"] for x in result.data]

        self.assertEqual(result_pub_dates, sorted_pub_dates)

    def test_invalid_sort_key(self):
        """Test sorting news with invalid sort key"""
        result = self.client.get(
            self.api_url, {"sort_by": "foobar"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_invalid_sort_key_but_no_news(self):
        """Test sorting news with invalid sort key"""
        result = self.client.get(
            self.api_url,
            {"project_ids": "9999", "sort_by": "foobar"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 0)
