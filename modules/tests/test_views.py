from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase
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
        )

    def test_version_latest(self):
        url = reverse("modules-release-detail", kwargs={"version": "latest"})

        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version"], "2.10.0")

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
