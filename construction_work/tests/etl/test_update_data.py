from unittest import mock

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from construction_work.etl.update_data import (
    _cleanup_inactive_projects,
    _deactivate_unseen_projects,
    _remove_unseen_articles,
    extract_transform_load,
    garbage_collector,
)
from construction_work.models.article_models import Article
from construction_work.models.project_models import Project


def mock_get_all_iprox_items(url):
    return [{"id": 1}, {"id": 2}, {"id": 3}]


def mock_get_iprox_items_data(*args, **kwargs):
    return [
        {"id": 1, "data": "Project 1 Data"},
        {"id": 2, "data": "Project 2 Data"},
        {"id": 3, "data": "Project 3 Data"},
    ]


def mock_transform_func(data):
    for item in data:
        item["transformed"] = True
    return data


def mock_load_func(data):
    pass


class ExtractTransformLoadTestCase(TestCase):
    @mock.patch(
        "construction_work.etl.update_data.get_iprox_items_data",
        side_effect=mock_get_iprox_items_data,
    )
    @mock.patch(
        "construction_work.etl.update_data.get_all_iprox_items",
        side_effect=mock_get_all_iprox_items,
    )
    def test_extract_transform_load(self, mock_get_all_items, mock_get_items_data):
        iprox_url = "http://example.com/api"
        result = extract_transform_load(
            iprox_url=iprox_url,
            transform_func=mock_transform_func,
            load_func=mock_load_func,
        )

        mock_get_all_items.assert_called_once_with(iprox_url)
        mock_get_items_data.assert_called_once_with(url=iprox_url, item_ids=[1, 2, 3])

        self.assertEqual(result, [1, 2, 3])

    @mock.patch(
        "construction_work.etl.update_data.get_iprox_items_data",
        side_effect=Exception("API Error"),
    )
    @mock.patch(
        "construction_work.etl.update_data.get_all_iprox_items",
        side_effect=mock_get_all_iprox_items,
    )
    def test_extract_transform_load_api_error(
        self, mock_get_all_items, mock_get_items_data
    ):
        iprox_url = "http://example.com/api"

        with self.assertRaises(Exception) as context:
            extract_transform_load(
                iprox_url=iprox_url,
                transform_func=mock_transform_func,
                load_func=mock_load_func,
            )

        self.assertEqual(str(context.exception), "API Error")


class GarbageCollectorTestCase(TestCase):
    def setUp(self):
        # Create some test projects and articles
        self.project1 = Project.objects.create(
            foreign_id=1,
            title="Project 1",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )
        self.project2 = Project.objects.create(
            foreign_id=2,
            title="Project 2",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )
        self.project_hidden = Project.objects.create(
            foreign_id=3,
            title="Hidden Project",
            active=True,
            hidden=True,  # Should not be deactivated or deleted
            last_seen=timezone.now(),
        )
        self.article1 = baker.make(Article, foreign_id=1, title="Article 1")
        self.article2 = baker.make(Article, foreign_id=2, title="Article 2")

    def test_garbage_collector(self):
        found_projects = [self.project1.foreign_id]  # Only project1 is found
        found_articles = [1]  # Only article1 is found

        self.project2.last_seen = timezone.now() - timezone.timedelta(days=6)
        self.project2.active = False
        self.project2.save(update_active=False)

        garbage_collector(found_projects, found_articles)

        self.project1.refresh_from_db()
        self.project2_exists = Project.objects.filter(foreign_id=2).exists()
        self.project_hidden.refresh_from_db()
        self.article1.refresh_from_db()
        self.article2_exists = Article.objects.filter(foreign_id=2).exists()

        self.assertTrue(self.project1.active)
        self.assertFalse(self.project2_exists)  # Should be deleted
        self.assertTrue(self.project_hidden.active)  # Should remain active
        self.assertTrue(self.article1 in Article.objects.all())
        self.assertFalse(self.article2_exists)  # Should be deleted

    def test_deactivate_unseen_projects(self):
        found_projects = [self.project1.foreign_id]
        _deactivate_unseen_projects(found_projects)

        self.project1.refresh_from_db()
        self.project2.refresh_from_db()
        self.project_hidden.refresh_from_db()

        self.assertTrue(self.project1.active)
        self.assertFalse(self.project2.active)
        self.assertTrue(
            self.project_hidden.active
        )  # Hidden projects should not be deactivated

    def test_cleanup_inactive_projects(self):
        self.project2.last_seen = timezone.now() - timezone.timedelta(days=6)
        self.project2.active = False
        self.project2.save(update_active=False)

        _cleanup_inactive_projects()

        project2_exists = Project.objects.filter(foreign_id=2).exists()
        self.assertFalse(project2_exists)
        project1_exists = Project.objects.filter(foreign_id=1).exists()
        self.assertTrue(project1_exists)

    def test_remove_unseen_articles(self):
        found_articles = [1]
        initial_article_count = _remove_unseen_articles(found_articles)

        # Check that article2 is deleted
        article2_exists = Article.objects.filter(foreign_id=2).exists()
        self.assertFalse(article2_exists)

        self.assertEqual(initial_article_count, 2)
        self.assertEqual(Article.objects.count(), 1)

    def test_garbage_collector_status_logging(self):
        found_projects = [self.project1.foreign_id]
        found_articles = [1]

        with self.assertLogs("construction_work.etl.update_data", level="INFO") as cm:
            garbage_collector(found_projects, found_articles)

        # Check that garbage_collector_status is logged
        logs = cm.output
        self.assertTrue(any("projects" in log for log in logs))
        self.assertTrue(any("articles" in log for log in logs))

    def test_deactivate_unseen_projects_transaction(self):
        found_projects = [self.project1.foreign_id]

        with mock.patch(
            "construction_work.etl.update_data.transaction.atomic"
        ) as mock_atomic:
            _deactivate_unseen_projects(found_projects)
            mock_atomic.assert_called_once()
