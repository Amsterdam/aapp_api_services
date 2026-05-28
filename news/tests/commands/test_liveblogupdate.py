
from django.core.management import call_command
from django.test import TestCase

from news.models import NewsArticle


class LiveblogUpdateTest(TestCase):
    def test_run_news_etl_no_liveblogs(self):
        call_command("liveblogupdate")

    def test_run_news_etl_no_active_liveblogs(self):
        NewsArticle.objects.create(
            foreign_id=123123,
            title="Test Liveblog",
            type="liveblog",
            is_active_liveblog=False,
        )

        call_command("liveblogupdate")

    def test_run_news_etl_with_active_liveblogs(self):
        NewsArticle.objects.create(
            foreign_id=123123,
            title="Test Liveblog",
            type="liveblog",
            is_active_liveblog=True,
        )

        call_command("liveblogupdate")
