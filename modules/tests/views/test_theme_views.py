from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase
from modules.icons import ModuleIconPath
from modules.models import AppRelease, Module, ReleaseModuleStatus
from modules.views.theme_views import MijnAmsterdamThemesStreamView


class TestMijnAmsterdamThemesView(BasicAPITestCase):
    def setUp(self):
        super().setUp()

        self.theme_module_1 = baker.make(
            Module,
            slug="theme-module-1",
            is_mams_theme=True,
        )
        self.theme_module_2 = baker.make(
            Module,
            slug="theme-module-2",
            is_mams_theme=True,
        )
        self.non_theme_module = baker.make(
            Module,
            slug="non-theme-module",
            is_mams_theme=False,
        )

        self.theme_module_1_version_1 = baker.make(
            "modules.ModuleVersion",
            module=self.theme_module_1,
            version="1.0.0",
        )
        self.theme_module_1_version_2 = baker.make(
            "modules.ModuleVersion",
            module=self.theme_module_1,
            version="1.2.0",
        )
        self.theme_module_2_version_1 = baker.make(
            "modules.ModuleVersion",
            module=self.theme_module_2,
            version="1.0.0",
        )
        self.non_theme_module_version_1 = baker.make(
            "modules.ModuleVersion",
            module=self.non_theme_module,
            version="1.0.0",
        )

        self.release_1 = baker.make(AppRelease, version="1.0.0")
        self.release_2 = baker.make(AppRelease, version="2.0.0")
        self.release_2_10 = baker.make(AppRelease, version="2.10.0")

    def test_version_latest(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "latest"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2_10,
            module_version=self.theme_module_1_version_2,
            sort_order=1,
        )

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["themes"]), 1)
        self.assertEqual(response.data["themes"][0]["moduleSlug"], "theme-module-1")
        self.assertEqual(
            response.data["themes"][0]["iconPath"],
            ModuleIconPath[self.theme_module_1_version_2.icon],
        )

    def test_version_specific(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "2.0.0"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.theme_module_1_version_1,
            sort_order=1,
        )
        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.non_theme_module_version_1,
            sort_order=2,
        )

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["themes"]), 1)
        self.assertEqual(response.data["themes"][0]["moduleSlug"], "theme-module-1")
        self.assertEqual(response.data["themes"][0]["status"], 1)

    def test_inactive_module(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "2.0.0"})

        self.theme_module_2.status = Module.Status.INACTIVE
        self.theme_module_2.save()
        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.theme_module_2_version_1,
            sort_order=1,
        )

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["themes"][0]["status"], 0)

    def test_inactive_release_version(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "2.0.0"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.theme_module_2_version_1,
            status=0,
            app_reason="Inactive release version",
            sort_order=1,
        )

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["themes"][0]["status"], 0)

    def test_get_release_without_auth_headers(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "2.0.0"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.theme_module_1_version_1,
            sort_order=1,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["themes"]), 1)

    def test_cache(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "latest"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2_10,
            module_version=self.theme_module_1_version_2,
            sort_order=1,
        )

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cache.keys("*")), 2)

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cache.keys("*")), 2)

    def test_latest_release_without_any_releases_returns_404(self):
        AppRelease.objects.all().delete()
        url = reverse("modules-themes-list", kwargs={"release_version": "latest"})

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)

    def test_missing_release_returns_404(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "9.9.9"})

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)


class TestMijnAmsterdamThemesStreamView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = MijnAmsterdamThemesStreamView()

    @override_settings(MIJN_AMS_HEADER_SESSION_ID="X-Mams-Session-Id")
    def test_get_returns_streaming_ndjson_response(self):
        request = self.factory.get("/", HTTP_X_MAMS_SESSION_ID="session-123")

        response = async_to_sync(self.view.get)(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/x-ndjson")
        self.assertEqual(self.view.session_id, "session-123")

    def test_event_generator_enriches_events_with_session_id(self):
        async def fake_consume_upstream_theme_stream(session_id):
            yield {"theme": "one"}

        self.view.consume_upstream_theme_stream = fake_consume_upstream_theme_stream

        async def collect_events():
            return [event async for event in self.view.event_generator("session-123")]

        events = async_to_sync(collect_events)()

        self.assertEqual(
            events,
            ['{"theme": "one", "session_id": "session-123"}\n'],
        )

    @patch("modules.views.theme_views.httpx.AsyncClient")
    def test_consume_upstream_theme_stream_filters_and_parses_events(
        self, async_client
    ):
        session_id = "session-123"

        client = MagicMock()
        async_client_cm = AsyncMock()
        async_client_cm.__aenter__.return_value = client
        async_client_cm.__aexit__.return_value = None
        async_client.return_value = async_client_cm

        response = MagicMock()
        response.raise_for_status = MagicMock()

        def aiter_lines():
            async def iterator():
                for line in [
                    "",
                    "event: keep-alive",
                    'data: {"theme": "one"}',
                    "data: ",
                    'data: {"theme": "two"}',
                ]:
                    yield line

            return iterator()

        response.aiter_lines = aiter_lines

        stream_cm = AsyncMock()
        stream_cm.__aenter__.return_value = response
        stream_cm.__aexit__.return_value = None
        client.stream.return_value = stream_cm

        async def collect_events():
            return [
                event
                async for event in self.view.consume_upstream_theme_stream(session_id)
            ]

        events = async_to_sync(collect_events)()

        self.assertEqual(events, [{"theme": "one"}, {"theme": "two"}])
        async_client.assert_called_once_with(timeout=None)
        client.stream.assert_called_once_with(
            "GET",
            "https://test.mijn.amsterdam.nl/api/v1/services/stream",
            headers={"Authorization": "Bearer token-for-session-session-123"},
        )
