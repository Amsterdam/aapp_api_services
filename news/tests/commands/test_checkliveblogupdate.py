import asyncio
from copy import deepcopy
from datetime import datetime
from unittest.mock import AsyncMock, call, patch

import aiohttp
from django.core.management import call_command
from django.test import SimpleTestCase
from django.utils import timezone
from model_bakery import baker

from core.services.notification_service import ScheduledNotification
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from core.utils.dvo_utils import DvOResponseError
from news.management.commands import checkliveblogupdate
from news.models import (
    LiveBlogItem,
    LiveblogNotification,
    NewsArticle,
)
from news.tests.mock_data.all_news import BLOG_ARTICLE_368


class LiveblogHasUpdateTest(SimpleTestCase):
    def test_handle_continues_after_dvo_query_failures(self):
        command = checkliveblogupdate.Command()
        liveblogs = [
            baker.prepare(
                NewsArticle,
                foreign_id=foreign_id,
                modification_datetime=None,
            )
            for foreign_id in range(1, 5)
        ]
        changed_date = {"nodeByID": {"changedDate": "2026-11-06T09:00:00+00:00"}}
        http_error = aiohttp.ClientResponseError(None, (), status=500)
        query_results = [
            http_error,
            changed_date,
            asyncio.TimeoutError(),
            changed_date,
            DvOResponseError("Invalid DvO response"),
            changed_date,
            {"nodeByID": {"id": 4}},
        ]

        with (
            patch.object(
                checkliveblogupdate.NewsArticle.objects,
                "filter",
                return_value=liveblogs,
            ),
            patch.object(
                command,
                "_run_query",
                new=AsyncMock(side_effect=query_results),
            ) as mock_query,
            patch.object(
                checkliveblogupdate, "transform", return_value=["transformed"]
            ),
            patch.object(checkliveblogupdate.data_loader, "load") as mock_load,
            self.assertLogs(checkliveblogupdate.logger, level="ERROR") as captured_logs,
        ):
            command.handle()

        self.assertEqual(
            mock_query.await_args_list,
            [
                call(checkliveblogupdate.blog_base_info.QUERY, 1),
                call(checkliveblogupdate.blog_base_info.QUERY, 2),
                call(checkliveblogupdate.blog_full_content.QUERY, 2),
                call(checkliveblogupdate.blog_base_info.QUERY, 3),
                call(checkliveblogupdate.blog_full_content.QUERY, 3),
                call(checkliveblogupdate.blog_base_info.QUERY, 4),
                call(checkliveblogupdate.blog_full_content.QUERY, 4),
            ],
        )
        mock_load.assert_called_once_with(["transformed"])
        self.assertEqual(
            {record.foreign_id for record in captured_logs.records},
            {1, 2, 3},
        )

    def test_liveblog_has_update_compares_timezone_naive_api_date(self):
        command = checkliveblogupdate.Command()
        liveblog = baker.prepare(
            NewsArticle,
            foreign_id=1234123,
            modification_datetime=datetime.fromisoformat("2026-11-03T09:18:04+00:00"),
        )

        with patch.object(
            command,
            "_run_query",
            new=AsyncMock(
                return_value={"nodeByID": {"changedDate": "2026-11-03T10:18:04"}}
            ),
        ) as mock_query:
            self.assertFalse(command.liveblog_has_update(liveblog))

        mock_query.assert_awaited_once_with(
            checkliveblogupdate.blog_base_info.QUERY, liveblog.foreign_id
        )

    def test_liveblog_has_update_returns_true_for_newer_api_date(self):
        command = checkliveblogupdate.Command()
        liveblog = baker.prepare(
            NewsArticle,
            foreign_id=1234123,
            modification_datetime=datetime.fromisoformat("2026-11-03T09:18:04+00:00"),
        )

        with patch.object(
            command,
            "_run_query",
            new=AsyncMock(
                return_value={"nodeByID": {"changedDate": "2026-11-03T10:19:04"}}
            ),
        ) as mock_query:
            self.assertTrue(command.liveblog_has_update(liveblog))

        mock_query.assert_awaited_once_with(
            checkliveblogupdate.blog_base_info.QUERY, liveblog.foreign_id
        )


class LiveblogUpdateTest(ResponsesActivatedAPITestCase):
    def _mock_liveblog_queries(self, include_image_update=False):
        full_blog = deepcopy(BLOG_ARTICLE_368)
        full_blog["id"] = 1234123
        full_blog["changedDate"] = "2026-10-02T08:27:17"
        full_blog["tag"].append({"id": 2696, "name": "Active liveblog"})

        for index, entry in enumerate(full_blog["blogEntries"]):
            entry["dateTime"] = f"2026-10-{3 - index:02d}T08:27:17"

        if include_image_update:
            full_blog["blogEntries"][0]["title"] = "Update with image"

        mock_query = AsyncMock(
            side_effect=[
                {"nodeByID": {"changedDate": "2026-10-02T08:27:17"}},
                {"nodeByID": full_blog},
            ]
        )
        return full_blog, mock_query

    def test_run_news_etl_no_liveblogs(self):
        """Test that the command runs without errors when there are no active liveblogs in the database."""
        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 0)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_news_etl_no_active_liveblogs(self):
        """Test that the command runs without errors when there are liveblogs in the database but none of them are active."""
        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=False,
        )

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_news_etl_with_active_liveblogs(self):
        """Test that the command runs without errors when there are active liveblogs in the database."""

        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
            liveblog_notification_send=timezone.now(),  # This is to test that no new liveblog notification is created
            modification_datetime=datetime.fromisoformat("2026-10-01T08:27:17+02:00"),
        )

        full_blog, mock_query = self._mock_liveblog_queries()
        with patch.object(checkliveblogupdate.Command, "_run_query", mock_query):
            call_command("checkliveblogupdate")

        mock_query.assert_has_awaits(
            [
                call(checkliveblogupdate.blog_base_info.QUERY, 1234123),
                call(checkliveblogupdate.blog_full_content.QUERY, 1234123),
            ]
        )
        self.assertEqual(mock_query.await_count, 2)
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), len(full_blog["blogEntries"]))
        self.assertEqual(
            ScheduledNotification.objects.count(), 0
        )  # There should be no notifications because the liveblog already exists in the database (so no new liveblog notification)

    def test_run_news_etl_with_active_liveblogs_and_notifications(
        self,
    ):
        """
        Test that the command runs without errors when there are active liveblogs in the database and there are people that want updates about the liveblogs.
        """

        article = baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
            liveblog_notification_send=timezone.now(),
            modification_datetime=datetime.fromisoformat("2026-10-01T08:27:17+02:00"),
        )

        baker.make(
            LiveblogNotification,
            article=article,
            device_id="device1",
        )

        full_blog, mock_query = self._mock_liveblog_queries(include_image_update=True)
        with patch.object(checkliveblogupdate.Command, "_run_query", mock_query):
            call_command("checkliveblogupdate")

        mock_query.assert_has_awaits(
            [
                call(checkliveblogupdate.blog_base_info.QUERY, 1234123),
                call(checkliveblogupdate.blog_full_content.QUERY, 1234123),
            ]
        )
        self.assertEqual(mock_query.await_count, 2)
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), len(full_blog["blogEntries"]))
        self.assertEqual(
            ScheduledNotification.objects.count(), len(full_blog["blogEntries"])
        )  # There should be a notification for each new liveblog item.

        notification_with_image = ScheduledNotification.objects.filter(
            body="Update with image"
        ).first()
        self.assertIsNotNone(notification_with_image)
