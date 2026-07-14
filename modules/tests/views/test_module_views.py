from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase, BasicInternalAPITestCase
from modules.icons import ModuleIconPath
from modules.models import AppRelease, Module, ReleaseModuleStatus


class TestReleaseDetailView(BasicAPITestCase):
    def setUp(self):
        super().setUp()

        self.module_1 = baker.make(Module, slug="module-1")
        self.module_2 = baker.make(Module, slug="module-2")

        self.module_1_version_1 = baker.make(
            "modules.ModuleVersion",
            module=self.module_1,
            version="1.0.0",
        )
        self.module_1_version_2 = baker.make(
            "modules.ModuleVersion",
            module=self.module_1,
            version="1.2.0",
        )
        self.module_2_version_1 = baker.make(
            "modules.ModuleVersion",
            module=self.module_2,
            version="1.0.0",
        )

        self.release_1 = baker.make(
            AppRelease,
            version="1.0.0",
        )
        self.release_2 = baker.make(
            AppRelease,
            version="2.0.0",
        )
        self.release_2_2 = baker.make(
            AppRelease,
            version="2.2.0",
        )
        self.release_2_10 = baker.make(
            AppRelease,
            version="2.10.0",
            modules=[self.module_1_version_2],
        )

    def test_version_latest(self):
        url = reverse("modules-release-detail", kwargs={"version": "latest"})

        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version"], "2.10.0")
        self.assertEqual(
            response.data["modules"][0]["iconPath"],
            ModuleIconPath[self.module_1_version_2.icon],
        )

    def test_version_specific(self):
        url = reverse("modules-release-detail", kwargs={"version": "2.0.0"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.module_1_version_1,
            sort_order=1,
        )
        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.module_2_version_1,
            sort_order=2,
        )

        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version"], "2.0.0")
        self.assertEqual(len(response.data["modules"]), 2)
        self.assertEqual(response.data["modules"][0]["moduleSlug"], "module-1")
        self.assertEqual(response.data["modules"][0]["status"], 1)
        self.assertEqual(response.data["modules"][1]["moduleSlug"], "module-2")
        self.assertEqual(response.data["modules"][1]["status"], 1)

    def test_inactive_module(self):
        url = reverse("modules-release-detail", kwargs={"version": "2.0.0"})

        self.module_2.status = Module.Status.INACTIVE
        self.module_2.save()
        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.module_2_version_1,
            sort_order=1,
        )

        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["modules"][0]["status"], 0)

    def test_inactive_release_version(self):
        url = reverse("modules-release-detail", kwargs={"version": "2.0.0"})

        baker.make(
            ReleaseModuleStatus,
            app_release=self.release_2,
            module_version=self.module_2_version_1,
            status=0,
            app_reason="Inactive release version",
            sort_order=1,
        )

        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["modules"][0]["status"], 0)

    def test_get_release_without_auth_headers(self):
        url = reverse("modules-release-detail", kwargs={"version": "2.0.0"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version"], "2.0.0")

    def test_cache(self):
        url = reverse("modules-release-detail", kwargs={"version": "latest"})

        # First call
        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(cache.keys("*")), 2
        )  # The request and the headers are cached both as separate keys

        # Second call
        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cache.keys("*")), 2)


class TestReleaseUpdateView(BasicInternalAPITestCase):
    def setUp(self):
        super().setUp()
        self.release = baker.make(
            AppRelease,
            version="1.0.0",
            published=None,
            deprecated=None,
            unpublished=None,
            release_notes="Some notes",
        )

    def test_patch_release_dates(self):
        url = reverse(
            "modules-release-detail", kwargs={"version": self.release.version}
        )

        payload = {
            "published": "2025-01-01T00:00:00Z",
            "deprecated": "2025-02-01T00:00:00Z",
            "unpublished": "2025-03-01T00:00:00Z",
            "release_notes": "ignored",
        }

        response = self.client.patch(
            url, payload, format="json", headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.release.refresh_from_db()
        self.assertIsNotNone(self.release.published)
        self.assertIsNotNone(self.release.deprecated)
        self.assertIsNotNone(self.release.unpublished)
        self.assertEqual(self.release.release_notes, "Some notes")

    def test_patch_non_existing_release(self):
        url = reverse("modules-release-detail", kwargs={"version": "9.9.9"})
        response = self.client.patch(url, {}, format="json", headers=self.api_headers)
        self.assertEqual(response.status_code, 404)

    def test_patch_requires_internal_api_key(self):
        url = reverse(
            "modules-release-detail", kwargs={"version": self.release.version}
        )

        response = self.client.patch(
            url,
            {"published": "2025-01-01T00:00:00Z"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)


class TestAppReleaseListView(BasicInternalAPITestCase):
    def setUp(self):
        super().setUp()

        self.release_1 = baker.make(
            AppRelease,
            version="1.0.0",
        )
        self.release_2 = baker.make(
            AppRelease,
            version="2.0.0",
        )

    def test_get_releases(self):
        url = reverse("modules-release-list")

        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["version"], "2.0.0")
        self.assertEqual(response.data[1]["version"], "1.0.0")
