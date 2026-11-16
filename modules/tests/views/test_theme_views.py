import json
from unittest.mock import patch

import responses
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from requests import Response

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from modules.icons import ModuleIconPath
from modules.models import AppRelease, Module, ReleaseModuleStatus
from modules.tests.mock_data import MOCK_DATA
from modules.views.theme_views import MijnAmsterdamThemesView


@patch.dict(
    "modules.views.theme_views.MAPPING",
    {
        "theme-module-1": ["MILIEUZONE"],
        "theme-module-2": ["MILIEUZONE"],
    },
    clear=True,
)
class TestMijnAmsterdamThemesView(ResponsesActivatedAPITestCase):
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
        self.api_headers = {**self.api_headers, "AccessToken": "dummy-access-token"}
        self.view = MijnAmsterdamThemesView()

    def _add_responses(self, status=200, json_data=MOCK_DATA):
        url = settings.MIJN_AMS_API_DOMAIN + settings.MIJN_AMS_ALL_PATH

        resp = responses.add(
            responses.GET,
            url,
            json=json_data,
            status=status,
        )

        return resp

    def test_version_latest(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "latest"})
        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2_10,
            module_version=self.theme_module_1_version_2,
            sort_order=1,
        )
        resp = self._add_responses()

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["themes"]), 1)
        self.assertEqual(response.data["themes"][0]["moduleSlug"], "theme-module-1")
        self.assertEqual(
            response.data["themes"][0]["iconPath"],
            ModuleIconPath[self.theme_module_1_version_2.icon],
        )
        self.assertEqual(resp.call_count, 1)

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

        resp = self._add_responses()

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["themes"]), 1)
        self.assertEqual(response.data["themes"][0]["moduleSlug"], "theme-module-1")
        self.assertEqual(response.data["themes"][0]["status"], 1)
        self.assertEqual(resp.call_count, 1)

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
        resp = self._add_responses()

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["themes"][0]["status"], 0)
        self.assertEqual(resp.call_count, 1)

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

        resp = self._add_responses()

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["themes"][0]["status"], 0)
        self.assertEqual(resp.call_count, 1)

    def test_get_release_without_auth_headers(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "2.0.0"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.theme_module_1_version_1,
            sort_order=1,
        )

        resp = self._add_responses()

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Access token is required.")
        self.assertEqual(resp.call_count, 0)

    def test_latest_release_without_any_releases_returns_404(self):
        AppRelease.objects.all().delete()
        url = reverse("modules-themes-list", kwargs={"release_version": "latest"})

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)

    def test_missing_release_returns_404(self):
        url = reverse("modules-themes-list", kwargs={"release_version": "9.9.9"})

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)

    @patch("modules.views.theme_views.requests.get")
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
            {"content": MOCK_DATA, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        resp = self.view._make_request("dummy-access-token")
        self.assertEqual(resp.status_code, 200)
