import json
from unittest.mock import patch
from urllib.parse import urljoin

import responses
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from model_bakery import baker
from requests import Response

from core.services.notification_service import ScheduledNotification
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from news.management.commands import checkliveblogupdate
from news.models import (
    LiveBlogItem,
    LiveblogNotification,
    NewsArticle,
)
from news.tests.mock_data import item_liveblog, liveblog_latest_version

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/")
IPROX_DETAIL_URL = urljoin(IPROX_URL, "item/")


class LiveblogUpdateTest(ResponsesActivatedAPITestCase):
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

    def test_run_news_etl_active_liveblogs_no_version_number(self):
        """Test that the command runs without errors when there are active liveblogs in the database but none of them have a version number."""
        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
        )

        # mock the response as invalid from the Iprox API for the latest version of the liveblog
        responses.get(urljoin(IPROX_DETAIL_URL, "1234123/latest-version"), status=503)

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_news_etl_active_liveblogs_no_valid_version_key(self):
        """Test that the command runs without errors when there are active liveblogs in the database but none of them have a version number."""
        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
        )

        # mock the response as invalid from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/latest-version"),
            status=200,
            json={"invalid_key": "invalid_value"},
        )

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_news_etl_active_liveblogs_no_valid_version_value(self):
        """Test that the command runs without errors when there are active liveblogs in the database but none of them have a version number."""
        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
        )

        # mock the response as invalid from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/latest-version"),
            status=200,
            json={"Vrs": "invalid_value"},
        )

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_news_etl_active_liveblogs_no_higher_version_number(self):
        """Test that the command runs without errors when there are active liveblogs in the database but none of them have a version number."""
        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
            liveblog_version=123,
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/latest-version"),
            status=200,
            json=liveblog_latest_version.MOCK_RESPONSE,
        )

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_run_news_etl_active_liveblogs_no_valid_liveblog_data(self):
        """Test that the command runs without errors when there are active liveblogs in the database but none of them have a version number."""
        baker.make(
            NewsArticle,
            foreign_id=1234123,
            title="Test Liveblog",
            is_liveblog=True,
            is_active_liveblog=True,
            liveblog_version=123,
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/latest-version"),
            status=200,
            json=liveblog_latest_version.MOCK_RESPONSE,
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/retrieve-version/123"),
            status=503,
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
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/latest-version"),
            status=200,
            json=liveblog_latest_version.MOCK_RESPONSE,
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/retrieve-version/123"),
            status=200,
            json=item_liveblog.MOCK_RESPONSE_1234123,
        )

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(
            LiveBlogItem.objects.count(), 19
        )  # There are 19 items in the mocked response
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
        )

        baker.make(
            LiveblogNotification,
            article=article,
            device_id="device1",
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/latest-version"),
            status=200,
            json=liveblog_latest_version.MOCK_RESPONSE,
        )

        # mock the response from the Iprox API for the latest version of the liveblog
        responses.get(
            urljoin(IPROX_DETAIL_URL, "1234123/retrieve-version/123"),
            status=200,
            json=item_liveblog.MOCK_RESPONSE_1234123,
        )

        call_command("checkliveblogupdate")
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(
            LiveBlogItem.objects.count(), 19
        )  # There are 19 items in the mocked response
        self.assertEqual(
            ScheduledNotification.objects.count(), 19
        )  # There should be a notification for each new liveblog item.

        notification_with_image = ScheduledNotification.objects.filter(
            body="Update with image"
        ).first()
        self.assertIsNotNone(notification_with_image)

    @patch("news.management.commands.checkliveblogupdate.requests.get")
    def test_make_request_succeeds_after_retry(self, mock_get):
        # Simulate a 500 error on the first request
        mock_response_1 = Response()
        mock_response_1.status_code = 500
        mock_response_1._content = json.dumps(
            {"status": "ERROR", "message": "Internal Server Error"}
        ).encode("utf-8")

        # Simulate a successful response on the second request
        mock_response_2 = Response()
        mock_response_2.status_code = 200
        mock_response_2._content = json.dumps(
            {"content": liveblog_latest_version.MOCK_RESPONSE, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        resp = checkliveblogupdate.Command()._make_request("some_url")
        self.assertEqual(resp.status_code, 200)
