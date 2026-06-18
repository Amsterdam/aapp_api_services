from unittest.mock import call, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker

from news.management.commands import runconstructionworketl
from news.models.article_models import NewsArticle
from news.models.project_models import (
    Project,
    ProjectContact,
    ProjectImage,
    ProjectSection,
    ProjectSectionUrl,
    ProjectTimelineItem,
)


class RunConstructionWorkETLTest(TestCase):
    def _article_payload(self, article_id):
        return {
            "id": article_id,
            "title": f"<div>Construction update {article_id}</div>",
            "body": "<div><p>Road closed.</p></div>",
            "summary": "<div><p>Summary.</p></div>",
            "intro": "<div><p>Intro.</p></div>",
            "district": None,
            "url": f"https://example.com/news/{article_id}",
            "created": "2024-01-01T12:00:00Z",
            "modified": "2024-01-01T13:00:00Z",
            "publicationDate": "2024-01-01T13:00:00Z",
            "image_url": "",
            "is_construction_work": True,
        }

    def _project_image(self):
        return {
            "id": 9001,
            "aspectRatio": "4:3",
            "alternativeText": "Bridge maintenance overview",
            "sources": [
                {
                    "uri": "https://example.com/project-small.jpg",
                    "width": "640",
                    "height": "480",
                },
                {
                    "uri": "https://example.com/project-large.jpg",
                    "width": "1200",
                    "height": "900",
                },
            ],
        }

    def _projects_payload(self, image_wrapper="image", section_links=None):
        section_links = section_links or []
        payload = {
            "id": 7001,
            "title": "Bridge maintenance",
            "subtitle": "Keep traffic moving",
            "url": "https://example.com/projects/7001",
            "created": "2024-01-01T12:00:00Z",
            "modified": "2024-01-02T12:00:00Z",
            "expirationDate": None,
            "timeline": {"title": "Timeline", "intro": "Intro", "items": []},
            "coordinates": {"lat": 52.37, "lon": 4.89},
            "sections": {
                "where": [
                    {
                        "title": "Where",
                        "body": "In Centrum",
                        "links": section_links,
                    }
                ],
                "what": [],
                "when": [],
                "work": [],
                "contact": [],
            },
            "contacts": [],
        }
        if image_wrapper == "image":
            payload["image"] = self._project_image()
        else:
            payload["images"] = [self._project_image()]
        return [payload]

    def _image_set_payload(self, image_set_id=12345):
        return {
            "id": image_set_id,
            "identifier": "project-image-set",
            "variants": [
                {
                    "image": "https://images.example.com/project-large.jpg",
                    "width": 1200,
                    "height": 900,
                },
                {
                    "image": "https://images.example.com/project-large@2x.jpg",
                    "width": 2400,
                    "height": 1800,
                },
            ],
        }

    def _run_etl(
        self,
        *,
        projects_payload=None,
        articles_payload=None,
        image_set_payload=None,
    ):
        with (
            patch(
                "news.etl.load_projects.IMAGE_SERVICE.get_or_upload_from_url"
            ) as mock_get_or_upload_from_url,
            patch(
                "news.management.commands.runconstructionworketl.iprox_fetcher.extract"
            ) as mock_extract,
        ):
            mock_get_or_upload_from_url.return_value = (
                image_set_payload or self._image_set_payload()
            )
            mock_extract.side_effect = [
                projects_payload or self._projects_payload(),
                articles_payload or self._articles_payload(),
            ]

            call_command("runconstructionworketl")

        return mock_extract, mock_get_or_upload_from_url

    def _assert_project_images(self):
        project = Project.objects.get(foreign_id=7001)
        self.assertEqual(ProjectImage.objects.filter(parent=project).count(), 2)
        self.assertEqual(
            list(
                ProjectImage.objects.filter(parent=project)
                .order_by("uri")
                .values_list("uri", flat=True)
            ),
            [
                "https://images.example.com/project-large.jpg",
                "https://images.example.com/project-large@2x.jpg",
            ],
        )
        self.assertTrue(
            ProjectImage.objects.filter(parent=project, foreign_id=12345).exists()
        )

    def _articles_payload(self, article_ids=None):
        article_ids = article_ids or [8001]
        return [self._article_payload(article_id) for article_id in article_ids]

    def _create_project_with_children(
        self,
        *,
        foreign_id,
        active,
        hidden,
        last_seen,
    ):
        project = Project.objects.create(
            foreign_id=foreign_id,
            title=f"Project {foreign_id}",
            url=f"https://example.com/projects/{foreign_id}",
            active=active,
            hidden=hidden,
            last_seen=last_seen,
        )
        contact = ProjectContact.objects.create(
            id=float(foreign_id),
            project=project,
            name="Resident contact",
        )
        section = ProjectSection.objects.create(
            project=project,
            title="Where",
            body="Centrum",
            type="where",
        )
        section_url = ProjectSectionUrl.objects.create(
            section=section,
            url="https://example.com/section-link",
            label="Section link",
        )
        timeline_item = ProjectTimelineItem.objects.create(
            project=project,
            title="Phase 1",
        )
        timeline_child = ProjectTimelineItem.objects.create(
            parent=timeline_item,
            title="Sub phase",
        )
        return {
            "project": project,
            "contact": contact,
            "section": section,
            "section_url": section_url,
            "timeline_item": timeline_item,
            "timeline_child": timeline_child,
        }

    def _assert_project_children_exist(self, seeded_project, *, exists):
        self.assertEqual(
            ProjectContact.objects.filter(id=seeded_project["contact"].id).exists(),
            exists,
        )
        self.assertEqual(
            ProjectSection.objects.filter(id=seeded_project["section"].id).exists(),
            exists,
        )
        self.assertEqual(
            ProjectSectionUrl.objects.filter(
                id=seeded_project["section_url"].id
            ).exists(),
            exists,
        )
        self.assertEqual(
            ProjectTimelineItem.objects.filter(
                id=seeded_project["timeline_item"].id
            ).exists(),
            exists,
        )
        self.assertEqual(
            ProjectTimelineItem.objects.filter(
                id=seeded_project["timeline_child"].id
            ).exists(),
            exists,
        )

    @patch("news.etl.load_projects.IMAGE_SERVICE.get_or_upload_from_url")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_persists_projects_and_articles(
        self, mock_extract, mock_get_or_upload_from_url
    ):
        mock_get_or_upload_from_url.return_value = self._image_set_payload()
        mock_extract.side_effect = [self._projects_payload(), self._articles_payload()]

        call_command("runconstructionworketl")

        self._assert_project_images()
        article = NewsArticle.objects.get(foreign_id=8001)
        self.assertTrue(article.is_construction_work)
        mock_get_or_upload_from_url.assert_called_once_with(
            "https://example.com/project-large.jpg"
        )

    @patch("news.etl.load_projects.IMAGE_SERVICE.get_or_upload_from_url")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_persists_project_images_from_images_wrapper(
        self, mock_extract, mock_get_or_upload_from_url
    ):
        mock_get_or_upload_from_url.return_value = self._image_set_payload()
        mock_extract.side_effect = [
            self._projects_payload(image_wrapper="images"),
            self._articles_payload(),
        ]

        call_command("runconstructionworketl")

        self._assert_project_images()
        mock_get_or_upload_from_url.assert_called_once_with(
            "https://example.com/project-large.jpg"
        )

    def test_run_construction_work_etl_persists_project_section_links(self):
        projects_payload = self._projects_payload(
            section_links=[
                {
                    "label": "Resident updates",
                    "url": "https://example.com/projects/7001/updates",
                }
            ]
        )

        self._run_etl(projects_payload=projects_payload)

        project = Project.objects.get(foreign_id=7001)
        section = ProjectSection.objects.get(project=project, type="where")
        self.assertEqual(
            list(section.links.values_list("label", "url")),
            [
                (
                    "Resident updates",
                    "https://example.com/projects/7001/updates",
                )
            ],
        )

    @patch("news.management.commands.runconstructionworketl.logger.info")
    @patch("news.management.commands.runconstructionworketl.logger.error")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_does_not_log_success_after_no_projects(
        self,
        mock_extract,
        mock_logger_error,
        mock_logger_info,
    ):
        mock_extract.return_value = []

        call_command("runconstructionworketl")

        mock_extract.assert_called_once_with(runconstructionworketl.IPROX_PROJECTS_URL)
        mock_logger_error.assert_called_once()
        self.assertNotIn(
            call("ETL process completed successfully."),
            mock_logger_info.call_args_list,
        )
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(NewsArticle.objects.count(), 0)

    @patch("news.management.commands.runconstructionworketl.logger.info")
    @patch("news.management.commands.runconstructionworketl.logger.error")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_short_circuits_when_no_articles(
        self,
        mock_extract,
        mock_logger_error,
        mock_logger_info,
    ):
        mock_extract.side_effect = [self._projects_payload(), []]

        call_command("runconstructionworketl")

        self.assertEqual(mock_extract.call_count, 2)
        self.assertTrue(Project.objects.filter(foreign_id=7001).exists())
        self.assertEqual(NewsArticle.objects.count(), 0)
        mock_logger_error.assert_called_once()
        self.assertNotIn(
            call("ETL process completed successfully."),
            mock_logger_info.call_args_list,
        )

    @patch(
        "news.management.commands.runconstructionworketl.transform_articles",
        return_value=[],
    )
    @override_settings(
        DELETE_UNSEEN_ARTICLES=True,
        DELETE_UNSEEN_ARTICLES_AFTER_SECONDS=7200,
    )
    @patch(
        "news.management.commands.runconstructionworketl.garbage_collect_unseen_articles"
    )
    @patch("news.management.commands.runconstructionworketl.logger.info")
    @patch("news.management.commands.runconstructionworketl.logger.error")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_logs_handled_transform_abort_without_success(
        self,
        mock_extract,
        mock_logger_error,
        mock_logger_info,
        mock_garbage_collect,
        mock_transform_articles,
    ):
        extracted_articles = self._articles_payload()
        mock_extract.side_effect = [self._projects_payload(), extracted_articles]

        call_command("runconstructionworketl")

        self.assertTrue(Project.objects.filter(foreign_id=7001).exists())
        self.assertEqual(NewsArticle.objects.count(), 0)
        mock_transform_articles.assert_called_once_with(extracted_articles)
        mock_logger_error.assert_called_once()
        self.assertIsInstance(
            mock_logger_error.call_args.kwargs["exc_info"],
            runconstructionworketl.ConstructionWorkETLError,
        )
        self.assertEqual(
            str(mock_logger_error.call_args.kwargs["exc_info"]),
            "No valid transformed articles found. Ending ETL process.",
        )
        mock_garbage_collect.assert_not_called()
        self.assertNotIn(
            call("ETL process completed successfully."),
            mock_logger_info.call_args_list,
        )

    @patch.object(
        runconstructionworketl.article_data_loader.new_liveblog_notification_service,
        "send",
    )
    def test_run_construction_work_etl_does_not_touch_unrelated_active_liveblogs(
        self,
        mock_send,
    ):
        active_liveblog = baker.make(
            NewsArticle,
            foreign_id=7997,
            title="Unrelated active liveblog",
            url="https://example.com/liveblogs/7997",
            is_liveblog=True,
            is_active_liveblog=True,
            liveblog_notification_send=None,
        )

        self._run_etl()

        active_liveblog.refresh_from_db()
        self.assertIsNone(active_liveblog.liveblog_notification_send)
        mock_send.assert_not_called()

    def test_run_construction_work_etl_refreshes_project_timeline_metadata_on_rerun(
        self,
    ):
        self._run_etl()

        updated_projects = self._projects_payload()
        updated_projects[0]["timeline"] = {
            "title": "Updated timeline",
            "intro": "Updated intro",
            "items": [],
        }

        self._run_etl(projects_payload=updated_projects)

        project = Project.objects.get(foreign_id=7001)
        self.assertEqual(project.timeline_title, "Updated timeline")
        self.assertEqual(project.timeline_intro, "Updated intro")

    def test_run_construction_work_etl_deactivates_unseen_visible_projects_only(self):
        Project.objects.create(
            foreign_id=7998,
            title="Existing visible project",
            url="https://example.com/projects/7998",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )
        Project.objects.create(
            foreign_id=7999,
            title="Existing hidden project",
            url="https://example.com/projects/7999",
            active=True,
            hidden=True,
            last_seen=timezone.now(),
        )

        self._run_etl()

        visible_project = Project.objects.get(foreign_id=7998)
        hidden_project = Project.objects.get(foreign_id=7999)
        self.assertFalse(visible_project.active)
        self.assertTrue(hidden_project.active)

    def test_run_construction_work_etl_deletes_stale_inactive_visible_projects(self):
        Project.objects.create(
            foreign_id=7998,
            title="Stale project",
            url="https://example.com/projects/7998",
            active=False,
            hidden=False,
            last_seen=timezone.now() - timezone.timedelta(days=6),
        )

        self._run_etl()

        self.assertFalse(Project.objects.filter(foreign_id=7998).exists())

    @override_settings(
        DELETE_UNSEEN_ARTICLES=True,
        DELETE_UNSEEN_ARTICLES_AFTER_SECONDS=7200,
    )
    def test_run_construction_work_etl_garbage_collects_after_update_only_rerun(
        self,
    ):
        self._run_etl()

        stale_article = baker.make(
            NewsArticle,
            foreign_id=999999,
            deleted=False,
            in_all_news=True,
        )
        NewsArticle.objects.filter(id=stale_article.id).update(
            last_seen=timezone.now() - timezone.timedelta(hours=3)
        )

        self._run_etl()

        stale_article.refresh_from_db()
        self.assertTrue(stale_article.deleted)

    @override_settings(
        DELETE_UNSEEN_ARTICLES=True,
        DELETE_UNSEEN_ARTICLES_AFTER_SECONDS=7200,
    )
    def test_run_construction_work_etl_garbage_collects_after_new_article_creation(
        self,
    ):
        self._run_etl()

        stale_article = baker.make(
            NewsArticle,
            foreign_id=999999,
            deleted=False,
            in_all_news=True,
        )
        NewsArticle.objects.filter(id=stale_article.id).update(
            last_seen=timezone.now() - timezone.timedelta(hours=3)
        )

        self._run_etl(articles_payload=self._articles_payload(article_ids=[8001, 8002]))

        stale_article.refresh_from_db()
        self.assertTrue(stale_article.deleted)

    def test_run_construction_work_etl_preserves_unseen_project_children_during_grace_period(
        self,
    ):
        unseen_project = self._create_project_with_children(
            foreign_id=7998,
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )

        self._run_etl()

        unseen_project["project"].refresh_from_db()
        self.assertFalse(unseen_project["project"].active)
        self._assert_project_children_exist(unseen_project, exists=True)

    def test_run_construction_work_etl_deletes_stale_project_children_with_project(
        self,
    ):
        stale_project = self._create_project_with_children(
            foreign_id=7998,
            active=False,
            hidden=False,
            last_seen=timezone.now() - timezone.timedelta(days=6),
        )

        self._run_etl()

        self.assertFalse(Project.objects.filter(foreign_id=7998).exists())
        self._assert_project_children_exist(stale_project, exists=False)

    def test_run_construction_work_etl_removes_project_images_when_image_disappears(
        self,
    ):
        self._run_etl()

        projects_payload = self._projects_payload()
        projects_payload[0].pop("image")

        _, mock_get_or_upload_from_url = self._run_etl(
            projects_payload=projects_payload,
        )

        project = Project.objects.get(foreign_id=7001)
        self.assertEqual(ProjectImage.objects.filter(parent=project).count(), 0)
        mock_get_or_upload_from_url.assert_not_called()

    def test_run_construction_work_etl_refreshes_image_set_foreign_id_for_reused_variants(
        self,
    ):
        self._run_etl(image_set_payload=self._image_set_payload(image_set_id=12345))

        self._run_etl(image_set_payload=self._image_set_payload(image_set_id=54321))

        project = Project.objects.get(foreign_id=7001)
        self.assertEqual(
            list(
                ProjectImage.objects.filter(parent=project)
                .values_list("foreign_id", flat=True)
                .distinct()
            ),
            [54321],
        )
