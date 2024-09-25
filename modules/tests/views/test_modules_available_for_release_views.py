import json

from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus
from modules.tests.setup import TestCaseWithAuth


class TestModulesAvailableForReleaseView(TestCaseWithAuth):
    def test_modules_available_for_release_1(self):
        """Test modules available for release"""
        response = self.client.get(
            "/modules/api/v1/modules/available-for-release/0.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
        )
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "moduleSlug": "slug0",
                "title": "title",
                "version": "1.2.20",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug0",
                "title": "title",
                "version": "1.2.3",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug1",
                "title": "title",
                "version": "1.3.4",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug2",
                "title": "title",
                "version": "1.30.4",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug3",
                "title": "title",
                "version": "2.10.2",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug4",
                "title": "title",
                "version": "10.3.2",
                "description": "description",
                "icon": "icon",
            },
        ]

        result = json.loads(response.content.decode("utf-8"))
        for i, exp_res_item in enumerate(expected_result):
            self.assertDictEqual(exp_res_item, result[i])

    def test_modules_available_for_release_2(self):
        """Test modules available for release"""
        response = self.client.get(
            "/modules/api/v1/modules/available-for-release/0.0.1",
            HTTP_AUTHORIZATION=self.jwt_token,
        )
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "moduleSlug": "slug0",
                "title": "title",
                "version": "1.2.20",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug0",
                "title": "title",
                "version": "1.2.3",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug1",
                "title": "title",
                "version": "1.3.4",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug2",
                "title": "title",
                "version": "1.30.4",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug3",
                "title": "title",
                "version": "2.10.2",
                "description": "description",
                "icon": "icon",
            },
            {
                "moduleSlug": "slug4",
                "title": "title",
                "version": "10.3.2",
                "description": "description",
                "icon": "icon",
            },
        ]

        result = json.loads(response.content.decode("utf-8"))
        for i, exp_res_item in enumerate(expected_result):
            self.assertDictEqual(exp_res_item, result[i])

    def test_modules_available_for_release_for_higher_or_equal_version(self):
        """Test if only modules unlinked or previously linked module versions are returned"""
        # Create new module
        module_foo_a = Module.objects.create(slug="foo_a")

        # Create module versions for new module
        version_1_0 = ModuleVersion.objects.create(
            module=module_foo_a,
            version="1.0.0",
            title="foo",
            description="foo",
            icon="foo",
        )
        version_1_1 = ModuleVersion.objects.create(
            module=module_foo_a,
            version="1.1.0",
            title="foo",
            description="foo",
            icon="foo",
        )
        version_2_0 = ModuleVersion.objects.create(
            module=module_foo_a,
            version="2.0.0",
            title="foo",
            description="foo",
            icon="foo",
        )
        version_2_1 = ModuleVersion.objects.create(
            module=module_foo_a,
            version="2.1.0",
            title="foo",
            description="foo",
            icon="foo",
        )

        # Create app release, to act as "previous" release,
        # and link a module version
        release_1_0 = AppRelease.objects.create(version="1.0.0", module_order=[])
        ReleaseModuleStatus.objects.create(
            app_release=release_1_0, module_version=version_1_1
        )

        # Create app release, to act as "current" release
        # Without any module versions connected to it yet
        release_2_0 = AppRelease.objects.create(version="2.0.0", module_order=[])

        # Get available module versions for the "current" release
        response = self.client.get(
            f"/modules/api/v1/modules/available-for-release/{release_2_0.version}",
            HTTP_AUTHORIZATION=self.jwt_token,
        )
        self.assertEqual(response.status_code, 200)

        # No RMS object should exist linked to module version 1.0
        rms_for_version_1_0 = ReleaseModuleStatus.objects.filter(
            module_version=version_1_0
        ).first()
        self.assertIsNone(rms_for_version_1_0)

        # Expect modules with equal or higher versions
        # then the version version that is connected to the latest release
        # - Module versions linked to the "previous" release should shown
        # - Module versions not yet linked to a release should shown
        expected_result = [
            {
                "moduleSlug": module_foo_a.slug,
                "title": version_1_1.title,
                "version": version_1_1.version,
                "description": version_1_1.description,
                "icon": version_1_1.icon,
            },
            {
                "moduleSlug": module_foo_a.slug,
                "title": version_2_0.title,
                "version": version_2_0.version,
                "description": version_2_0.description,
                "icon": version_2_0.icon,
            },
            {
                "moduleSlug": module_foo_a.slug,
                "title": version_2_1.title,
                "version": version_2_1.version,
                "description": version_2_1.description,
                "icon": version_2_1.icon,
            },
        ]

        result = json.loads(response.content.decode("utf-8"))
        for i, exp_res_item in enumerate(expected_result):
            self.assertDictEqual(exp_res_item, result[i])
