from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from model_bakery import baker

from construction_work.etl import update_data
from construction_work.etl.update_data import (
    _cleanup_inactive_projects,
    _deactivate_unseen_articles,
    _deactivate_unseen_projects,
    garbage_collector,
)
from construction_work.models.article_models import Article
from construction_work.models.project_models import Project


class ExtractTransformLoadTestCase(SimpleTestCase):
    def test_extract_transform_load(self):
        extracted = {
            "projects": [{"id": 101}],
            "news_articles": {501: [{"id": 201}, {"id": 202}]},
        }
        transformed = {"projects": [{"id": 101}], "articles": []}

        with (
            mock.patch.object(
                update_data,
                "get_all_drupal_projects_with_content",
                return_value=extracted,
            ) as extract,
            mock.patch.object(
                update_data, "transform_data", return_value=transformed
            ) as transform,
            mock.patch.object(update_data, "load_data") as load,
            self.assertLogs("construction_work.etl.update_data", level="INFO") as logs,
        ):
            result = update_data.extract_transform_load()

        extract.assert_called_once_with()
        transform.assert_called_once_with(extracted)
        load.assert_called_once_with(transformed)
        self.assertEqual(result, ([101], [201, 202]))
        self.assertTrue(
            any("Loaded data into Construction-Work" in line for line in logs.output)
        )


class GarbageCollectorTestCase(TestCase):
    def setUp(self):
        # Create some test projects and articles
        self.project1 = Project.objects.create(
            foreign_id=1,
            drupal_id=101,
            title="Project 1",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )
        self.project2 = Project.objects.create(
            foreign_id=2,
            drupal_id=102,
            title="Project 2",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )
        self.project_hidden = Project.objects.create(
            foreign_id=3,
            drupal_id=103,
            title="Hidden Project",
            active=True,
            hidden=True,  # Should not be deactivated or deleted
            last_seen=timezone.now(),
        )
        self.article1 = baker.make(
            Article, foreign_id=1, drupal_id=201, title="Article 1"
        )
        self.article2 = baker.make(
            Article, foreign_id=2, drupal_id=202, title="Article 2"
        )

    def test_garbage_collector(self):
        found_projects = [self.project1.drupal_id]  # Only project1 is found
        found_articles = [self.article1.drupal_id]  # Only article1 is found

        self.project2.last_seen = timezone.now() - timezone.timedelta(days=6)
        self.project2.active = False
        self.project2.save(update_active=False)

        garbage_collector(found_projects, found_articles)

        self.project1.refresh_from_db()
        self.project2_exists = Project.objects.filter(drupal_id=102).exists()
        self.project_hidden.refresh_from_db()
        self.article1.refresh_from_db()
        self.article2.refresh_from_db()

        self.assertTrue(self.project1.active)
        self.assertFalse(self.project2_exists)  # Should be deleted
        self.assertTrue(self.project_hidden.active)  # Should remain active
        self.assertTrue(self.article1 in Article.objects.all())
        self.assertFalse(self.article2.active)  # Should be inactive

    def test_deactivate_unseen_projects(self):
        found_projects = [self.project1.drupal_id]
        _deactivate_unseen_projects(found_projects)

        self.project1.refresh_from_db()
        self.project2.refresh_from_db()
        self.project_hidden.refresh_from_db()

        self.assertTrue(self.project1.active)
        self.assertFalse(self.project2.active)
        self.assertTrue(
            self.project_hidden.active
        )  # Hidden projects should not be deactivated

    def test_deactivate_legacy_project_without_drupal_id(self):
        legacy_project = Project.objects.create(
            foreign_id=4,
            title="Legacy project",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )

        _deactivate_unseen_projects([self.project1.drupal_id])

        legacy_project.refresh_from_db()
        self.assertFalse(legacy_project.active)

    def test_cleanup_inactive_projects(self):
        self.project2.last_seen = timezone.now() - timezone.timedelta(days=6)
        self.project2.active = False
        self.project2.save(update_active=False)

        _cleanup_inactive_projects()

        project2_exists = Project.objects.filter(drupal_id=102).exists()
        self.assertFalse(project2_exists)
        project1_exists = Project.objects.filter(drupal_id=101).exists()
        self.assertTrue(project1_exists)

    def test_deactivate_unseen_articles(self):
        found_articles = [self.article1.drupal_id]
        _deactivate_unseen_articles(found_articles)
        self.article2.refresh_from_db()

        # Check that article2 is deleted
        article2_exists = Article.objects.filter(drupal_id=202).exists()
        self.assertTrue(article2_exists)
        self.assertFalse(self.article2.active)

    def test_deactivate_legacy_article_without_drupal_id(self):
        legacy_article = baker.make(Article, foreign_id=3, drupal_id=None, active=True)

        _deactivate_unseen_articles([self.article1.drupal_id])

        legacy_article.refresh_from_db()
        self.assertFalse(legacy_article.active)

    def test_garbage_collector_status_logging(self):
        found_projects = [self.project1.drupal_id]
        found_articles = [self.article1.drupal_id]

        with self.assertLogs("construction_work.etl.update_data", level="INFO") as cm:
            garbage_collector(found_projects, found_articles)

        # Check that garbage_collector_status is logged
        logs = cm.output
        self.assertTrue(any("projects" in log for log in logs))
        self.assertTrue(any("articles" in log for log in logs))

    def test_deactivate_unseen_projects_transaction(self):
        found_projects = [self.project1.drupal_id]

        with mock.patch(
            "construction_work.etl.update_data.transaction.atomic"
        ) as mock_atomic:
            _deactivate_unseen_projects(found_projects)
            mock_atomic.assert_called_once()
