import json
from datetime import datetime

from django.urls import reverse

from construction_work.models import Article, Project
from construction_work.tests import mock_data
from construction_work.tests.test_project_views import BaseTestProjectView
from construction_work.utils.date_utils import translate_timezone as tt


class TestArticleDetailView(BaseTestProjectView):
    def setUp(self):
        """Setup test db"""
        super().setUp()
        self.api_url = reverse("construction-work-get-article")

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
            "image": article.image,
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
