from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from construction_work.etl.load_data import load_articles, load_projects
from construction_work.models.article_models import Article
from construction_work.models.project_models import Project


class ImageIngestionTests(TestCase):
    def test_project_and_article_variants_use_image_service_ids(self):
        project = baker.make(Project, foreign_id=42, drupal_id=142)
        article = baker.make(Article, foreign_id=43, drupal_id=143)
        now = timezone.now()
        common_data = {
            "title": "Updated content",
            "url": "https://example.com/content",
            "creation_date": now,
            "modification_date": now,
            "publication_date": now,
            "expiration_date": None,
            "image_set": {
                "id": 123,
                "variants": [
                    {
                        "uri": "https://example.com/large.jpg",
                        "width": 200,
                        "height": 100,
                    },
                    {
                        "uri": "https://example.com/small.jpg",
                        "width": 100,
                        "height": 50,
                    },
                ],
            },
        }

        for _ in range(2):
            load_projects([{**common_data, "id": project.drupal_id}])
            load_articles(
                [
                    {
                        **common_data,
                        "id": article.drupal_id,
                        "projectIds": [project.drupal_id],
                    }
                ]
            )
            for parent in (project, article):
                parent.refresh_from_db()
                self.assertEqual(
                    list(
                        parent.images.order_by("width").values_list(
                            "foreign_id", "uri", "width", "height"
                        )
                    ),
                    [
                        (123, "https://example.com/small.jpg", 100, 50),
                        (123, "https://example.com/large.jpg", 200, 100),
                    ],
                )
            self.assertEqual(project.drupal_id, 142)
            self.assertEqual(article.drupal_id, 143)
            self.assertEqual(list(article.projects.all()), [project])
