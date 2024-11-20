from modules.models import ReleaseModuleStatus
from modules.tests.setup import TestCaseWithAuth


class TestModuleVersionStatusView(TestCaseWithAuth):
    """tests for /api/v1/module"""

    def test_module_version_status_patch_200(self):
        """Test /api/v1/module/{slug}/version/{version}/status 200"""
        module_slug = "slug0"
        module_version = "1.2.3"
        release_version_0_0_1 = "0.0.1"
        release_version_0_0_2 = "0.0.2"

        # Start off with setting one status to inactive
        rms_0_0_1 = ReleaseModuleStatus.objects.get(
            module_version__module__slug=module_slug,
            module_version__version=module_version,
            app_release__version=release_version_0_0_1,
        )
        rms_0_0_1.status = 0
        rms_0_0_1.save()

        # And one status to active
        rms_0_0_2 = ReleaseModuleStatus.objects.get(
            module_version__module__slug=module_slug,
            module_version__version=module_version,
            app_release__version=release_version_0_0_2,
        )
        rms_0_0_2.status = 1
        rms_0_0_2.save()

        patch_data = [{"status": 1, "releases": [release_version_0_0_1]}]
        response = self.client.patch(
            f"/modules/api/v1/module/{module_slug}/version/{module_version}/status",
            data=patch_data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        self.assertEqual(response.status_code, 200)

        expected_result = [{"status": 1, "releases": ["0.0.1", "0.0.2"]}]
        self.assertEqual(len(response.data), 1)
        self.assertDictEqual(response.data[0], expected_result[0])

        # Expect RMS for version 0.0.1 to be now active
        rms_0_0_1.refresh_from_db()
        self.assertEqual(rms_0_0_1.status, 1)

        # Just like RMS for version 0.0.2 to still be active
        rms_0_0_2.refresh_from_db()
        self.assertEqual(rms_0_0_2.status, 1)

    def test_module_version_status_patch_404(self):
        """Test /api/v1/module/{slug}/version/{version}/status 404"""
        data = []
        response = self.client.patch(
            "/modules/api/v1/module/bogus/version/0.0.0/status",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

    def test_module_version_status_patch_400(self):
        """Test /api/v1/module/{slug}/version/{version}/status 400"""
        data = [{"status": 1, "releases": ["1.0.0"]}]
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3/status",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)
