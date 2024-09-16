# pylint: disable=too-many-lines
import json
from copy import copy
from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import Client, TestCase

from modules.models import (AppRelease, Module, ModuleVersion,
                            ReleaseModuleStatus)
from modules.unit_tests.tests_isauthorized import (mock_private_key,
                                                   mock_public_key)
from modules.unit_tests.unit_test_mock_data import TestData

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class BaseViewTest(TestCase):
    def setUp(self):
        # Setup the mock signing key
        patcher = patch('modules.generic_functions.is_authorized.IsAuthorized.get_signing_key')
        self.mock_get_signing_key = patcher.start()
        self.mock_get_signing_key.return_value = mock_public_key
        self.addCleanup(patcher.stop)

        # Add mock token and client
        payload = {
            "iss": f"https://sts.windows.net/{settings.TENANT_ID}/",
            "aud": f"api://{settings.CLIENT_ID}",
            "scp": "Modules.Edit"
        }
        self.jwt_token = "Bearer " + jwt.encode(payload, mock_private_key, algorithm="RS256")
        self.client = Client()

        self.data = TestData()
        self.maxDiff = None

        modules: list[Module] = []
        module_versions: list[ModuleVersion] = []
        releases: list[AppRelease] = []

        ## Create modules

        for module in self.data.modules:
            module = Module.objects.create(**module)
            modules.append(module)

        ## Link modules versions to modules

        first_version = self.data.module_versions[0]
        first_version["module"] = modules[0]
        first_version = ModuleVersion.objects.create(**first_version)
        module_versions.append(first_version)

        second_version = self.data.module_versions[1]
        second_version["module"] = modules[0]
        second_version = ModuleVersion.objects.create(**second_version)
        module_versions.append(second_version)

        third_version = self.data.module_versions[2]
        third_version["module"] = modules[1]
        third_version = ModuleVersion.objects.create(**third_version)
        module_versions.append(third_version)

        fourth_version = self.data.module_versions[3]
        fourth_version["module"] = modules[2]
        fourth_version = ModuleVersion.objects.create(**fourth_version)
        module_versions.append(fourth_version)

        fifth_version = self.data.module_versions[4]
        fifth_version["module"] = modules[3]
        fifth_version = ModuleVersion.objects.create(**fifth_version)
        module_versions.append(fifth_version)

        sixth_version = self.data.module_versions[5]
        sixth_version["module"] = modules[4]
        sixth_version = ModuleVersion.objects.create(**sixth_version)
        module_versions.append(sixth_version)

        ## Create releases

        for release in self.data.releases:
            release = AppRelease.objects.create(**release)
            releases.append(release)

        ## Link module versions to releases

        release_module_status_template = {
            "app_release": None,
            "module_version": None,
            "status": 1,
        }

        # app release 0.0.1
        first_release = copy(release_module_status_template)
        first_release["app_release"] = releases[1]
        first_release["module_version"] = module_versions[0]
        ReleaseModuleStatus.objects.create(**first_release)

        # app release 0.0.1
        second_release = copy(release_module_status_template)
        second_release["app_release"] = releases[1]
        second_release["module_version"] = module_versions[2]
        ReleaseModuleStatus.objects.create(**second_release)

        # app release 0.0.1
        third_release = copy(release_module_status_template)
        third_release["app_release"] = releases[1]
        third_release["module_version"] = module_versions[3]
        ReleaseModuleStatus.objects.create(**third_release)

        # app release 0.0.1
        fourth_release = copy(release_module_status_template)
        fourth_release["app_release"] = releases[1]
        fourth_release["module_version"] = module_versions[4]
        ReleaseModuleStatus.objects.create(**fourth_release)

        # app release 0.0.2
        fifth_release = copy(release_module_status_template)
        fifth_release["app_release"] = releases[2]
        fifth_release["module_version"] = module_versions[0]
        ReleaseModuleStatus.objects.create(**fifth_release)

        # app release 0.1.1
        sixth_release = copy(release_module_status_template)
        sixth_release["app_release"] = releases[3]
        sixth_release["module_version"] = module_versions[1]
        ReleaseModuleStatus.objects.create(**sixth_release)

        # app release 0.0.0
        seventh_release = copy(release_module_status_template)
        seventh_release["app_release"] = releases[0]
        seventh_release["module_version"] = module_versions[5]
        ReleaseModuleStatus.objects.create(**seventh_release)


class TestModuleViews(BaseViewTest):
    """Test '/module' view"""

    def test_get_module_with_versions_by_slug(self):
        """Get existing module with versions by slug"""
        module_slug = "slug0"
        module = Module.objects.filter(slug=module_slug).first()
        module_version_data = {
            "module": module,
            "title": "some title",
            "icon": "some icon",
            "version": "1.2.4",
            "description": "some description",
        }
        ModuleVersion.objects.create(**module_version_data)

        response = self.client.get(f"/modules/api/v1/module/{module_slug}", HTTP_AUTHORIZATION=self.jwt_token)
        expected_result = {
            "slug": "slug0",
            "status": 1,
            "versions": [
                {
                    "moduleSlug": "slug0",
                    "title": "title",
                    "icon": "icon",
                    "version": "1.2.20",
                    "description": "description",
                    "statusInReleases": [{"status": 1, "releases": ["0.1.1"]}],
                },
                {
                    "title": "some title",
                    "moduleSlug": "slug0",
                    "description": "some description",
                    "version": "1.2.4",
                    "icon": "some icon",
                    "statusInReleases": [],
                },
                {
                    "title": "title",
                    "moduleSlug": "slug0",
                    "description": "description",
                    "version": "1.2.3",
                    "icon": "icon",
                    "statusInReleases": [{"status": 1, "releases": ["0.0.1", "0.0.2"]}],
                },
            ],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict(response.data), expected_result)

    def test_module_slug_bogus(self):
        """get module by slug and version (exists)"""
        response = self.client.get(
            "/modules/api/v1/module/bogus",
            HTTP_AUTHORIZATION=self.jwt_token
        )
        expected_result = {"message": "Module with slug 'bogus' not found."}
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_module_post_ok(self):
        """test create new module"""
        new_slug = "new"
        data = {"slug": new_slug, "status": 1}
        response = self.client.post(
            "/modules/api/v1/module",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": {"slug": "new", "status": 1}}
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

        new_module = Module.objects.filter(slug=new_slug).first()
        self.assertIsNotNone(new_module)

    def test_module_post_incorrect_request_body(self):
        """test incorrect request body"""
        data = {}
        response = self.client.post(
            "/modules/api/v1/module",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "This field is required", status_code=400)

    def test_module_post_integrity_error(self):
        """test integrity error"""
        data = {"slug": "slug0", "status": 1}
        response = self.client.post(
            "/modules/api/v1/module",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response, "module with this slug already exists", status_code=400
        )

    def test_module_patch_ok(self):
        """test module patch ok"""
        slug = "slug0"
        updated_status = 0
        data = {"status": updated_status}
        response = self.client.patch(
            f"/modules/api/v1/module/{slug}",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        expected_result = {"message": {"slug": slug, "status": updated_status}}
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

        module = Module.objects.filter(slug=slug).first()
        self.assertEqual(module.status, updated_status)

    def test_module_patch_with_empty_request_body(self):
        """test incorrect request body"""
        data = {}
        response = self.client.patch(
            "/modules/api/v1/module/slug0",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Data may not be empty", status_code=400)

    def test_module_patch_module_not_found(self):
        """test patch but module not found"""
        data = {"status": 1}
        response = self.client.patch(
            "/modules/api/v1/module/bogus",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Module with slug 'bogus' not found."}
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_module_delete_with_active_module_version(self):
        """test delete model in use"""
        slug = "slug0"
        response = self.client.delete(
            f"/modules/api/v1/module/{slug}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": f"Cannot delete module with slug '{slug}' while it has versions"
        }
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.data, expected_result)

    def test_module_delete_ok(self):
        """test module delete ok"""
        new_slug = "new"
        data = {"slug": new_slug, "status": 1}
        Module.objects.create(**data)

        response = self.client.delete(
            f"/modules/api/v1/module/{new_slug}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, None)

        module = Module.objects.filter(slug=new_slug).first()
        self.assertIsNone(module)

    def test_modules_latest(self):
        """test modules/latest"""
        response = self.client.get(
            "/modules/api/v1/modules/latest",
            HTTP_AUTHORIZATION=self.jwt_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)


class TestModuleVersionViews(BaseViewTest):
    """
    Test the module version views.
    """

    def test_module_slug_version_post_ok(self):
        """test integrity error"""
        module_slug = "slug0"
        version = "2.3.4"
        data = {
            "moduleSlug": module_slug,
            "title": "string",
            "version": version,
            "description": "string",
            "icon": "icon",
        }

        module_version = ModuleVersion.objects.filter(
            module__slug=module_slug, version=version
        ).first()
        self.assertIsNone(module_version)

        response = self.client.post(
            f"/modules/api/v1/module/{module_slug}/version",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, data)

        module_version = ModuleVersion.objects.filter(
            module__slug=module_slug, version=version
        ).first()
        self.assertIsNotNone(module_version)

    def test_module_slug_version_post_incorrect_request_body_1(self):
        """test incorrect request body"""
        data = {}
        response = self.client.post(
            "/modules/api/v1/module/string/version",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Module with slug 'string' not found."}
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_post_integrity_error_1(self):
        """test integrity error"""
        data = {
            "moduleSlug": "slug0",
            "title": "string",
            "version": "1.2.3",
            "description": "string",
            "icon": "icon",
        }
        response = self.client.post(
            "/modules/api/v1/module/slug0/version",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": "Module with slug 'slug0' and version '1.2.3' already exists."
        }
        self.assertEqual(response.status_code, 409)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_post_integrity_error_2(self):
        """test integrity error"""
        data = {
            "moduleSlug": "bogus",
            "title": "string",
            "version": "2.3.4",
            "description": "string",
            "icon": "icon",
        }
        response = self.client.post(
            "/modules/api/v1/module/bogus/version",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Module with slug 'bogus' not found."}
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_post_incorrect_version_1(self):
        """test integrity error"""
        data = {
            "moduleSlug": "slug0",
            "title": "string",
            "version": "1.2.3a",
            "description": "string",
            "icon": "icon",
        }
        response = self.client.post(
            "/modules/api/v1/module/slug0/version",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Incorrect request version formatting."}
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_post_incorrect_version_2(self):
        """test integrity error"""
        data = {
            "moduleSlug": "slug0",
            "title": "string",
            "version": "1.2.3.4",
            "description": "string",
            "icon": "icon",
        }
        response = self.client.post(
            "/modules/api/v1/module/slug0/version",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Incorrect request version formatting."}
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_patch_ok(self):
        """Test patching the version of a module version"""
        module_data = {"slug": "slug10", "status": 1}
        module = Module.objects.create(**module_data)

        module_version_data = {
            "module": module,
            "title": "title",
            "icon": "icon",
            "version": "9.9.9",
            "description": "description",
        }
        new_module_version = ModuleVersion.objects.create(**module_version_data)

        updated_version = "4.6.7"
        data = {"version": updated_version}
        response = self.client.patch(
            "/modules/api/v1/module/slug10/version/9.9.9",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "moduleSlug": "slug10",
            "title": "title",
            "version": updated_version,
            "description": "description",
            "icon": "icon",
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

        updated_module_version = ModuleVersion.objects.get(
            module=module, version=updated_version
        )
        self.assertEqual(new_module_version.pk, updated_module_version.pk)

    def test_module_slug_version_patch_incorrect_request_body_1(self):
        """test incorrect request body"""
        data = {"moduleSlug": "slug0", "version": "3.4.5"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Incorrect request body."}
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_patch_not_found(self):
        """test incorrect request body"""
        data = {}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/3.4.5",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": "Module with slug 'slug0' and version '3.4.5' not found."
        }
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_patch_incorrect_version(self):
        """test incorrect request body"""
        data = {"version": "3.4.5a"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": "Incorrect request version formatting."}
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_patch_in_use_1(self):
        """test incorrect request body"""
        data = {"version": "10.11.12"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": "Module with slug 'slug0' and version '1.2.3' in use by release '0.0.1'."
        }
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_patch_in_use_2(self):
        """test incorrect request body"""
        data = {"description": "test"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "moduleSlug": "slug0",
            "title": "title",
            "version": "1.2.3",
            "description": "test",
            "icon": "icon",
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_patch_integrity_error(self):
        """test incorrect request body"""
        module = Module.objects.filter(slug="slug0").first()
        data = {"version": "1.2.3"}
        _module_version = {
            "module": module,
            "title": "title",
            "icon": "icon",
            "version": "9.9.9",
            "description": "description",
        }
        ModuleVersion.objects.create(**_module_version)
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/9.9.9",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": "Module with slug 'slug0' and version '1.2.3' already exists."
        }
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_delete_ok(self):
        """Create new module and delete it"""
        slug = "slug999"
        version = "1.0.0"

        module = Module(slug=slug)
        module.save()

        module_version = ModuleVersion(
            module=module,
            version=version,
            title="foobar",
            icon="foobar",
            description="foobar",
        )
        module_version.save()

        response = self.client.delete(
            f"/modules/api/v1/module/{slug}/version/{version}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        module_version = ModuleVersion.objects.filter(
            module__slug=slug, version=version
        ).first()
        self.assertIsNone(module_version)

    def test_module_slug_version_delete_not_found(self):
        """test incorrect request body"""
        response = self.client.delete(
            "/modules/api/v1/module/slug0/version/4.5.6",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": "Module with slug 'slug0' and version '4.5.6' not found."
        }
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_module_slug_version_delete_in_use(self):
        """test incorrect request body"""
        response = self.client.delete(
            "/modules/api/v1/module/slug0/version/1.2.3",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": "Module with slug 'slug0' is being used in a release."
        }
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.data, expected_result)

    def test_module_version_get_exist(self):
        """get module by slug and version (exists)"""
        response = self.client.get(
            "/modules/api/v1/module/slug0/version/1.2.3",
            HTTP_AUTHORIZATION=self.jwt_token
        )
        expected_result = {
            "moduleSlug": "slug0",
            "title": "title",
            "icon": "icon",
            "version": "1.2.3",
            "description": "description",
            "statusInReleases": [{"status": 1, "releases": ["0.0.1", "0.0.2"]}],
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

    def test_module_version_get_does_not_exist(self):
        """get module by slug and version (does not exist)"""
        response = self.client.get(
            "/modules/api/v1/module/bogus0/version/0.0.0",
            HTTP_AUTHORIZATION=self.jwt_token
        )
        expected_result = {
            "message": "Module with slug 'bogus0' and version '0.0.0' not found."
        }
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)


class TestModulesAvailableForReleaseView(BaseViewTest):
    def test_modules_available_for_release_1(self):
        """Test modules available for release"""
        response = self.client.get(
            "/modules/api/v1/modules/available-for-release/0.0.0",
            HTTP_AUTHORIZATION=self.jwt_token
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
            HTTP_AUTHORIZATION=self.jwt_token
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
            HTTP_AUTHORIZATION=self.jwt_token
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


class TestModuleVersionStatusView(BaseViewTest):
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
        expected_result = {
            "message": "Module with slug 'bogus' and version '0.0.0' not found."
        }
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

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
        expected_result = {
            "message": "Specified a release that doesn't contain the module version or doesn't even exist."
        }
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, expected_result)


class TestReleaseViews(BaseViewTest):
    def test_release_get_200(self):
        """Test get release existing"""
        response = self.client.get(
            "/modules/api/v1/release/0.0.1",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        expected_result = {
            "version": "0.0.1",
            "releaseNotes": "release 0.0.1",
            "isSupported": False,
            "isDeprecated": False,
            "published": "1971-01-01",
            "unpublished": "1971-12-31",
            "deprecated": None,
            "created": str(response.data["created"]),
            "modified": str(response.data["modified"]),
            "modules": [
                {
                    "moduleSlug": "slug0",
                    "version": "1.2.3",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
                {
                    "moduleSlug": "slug1",
                    "version": "1.3.4",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
                {
                    "moduleSlug": "slug2",
                    "version": "1.30.4",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
                {
                    "moduleSlug": "slug3",
                    "version": "2.10.2",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
            ],
            "latestVersion": "0.1.1",
            "latestReleaseNotes": "release 0.1.1",
        }


        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_result, response.data)

    def test_release_get_404(self):
        """Test get release not existing"""
        response = self.client.get(
            "/modules/api/v1/release/10.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(
            response.data, {"message": "Release version does not exist."}
        )

    def test_release_get_404_2(self):
        """Test get release not existing"""
        AppRelease.objects.filter().delete()
        response = self.client.get(
            "/modules/api/v1/release/latest",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, {"message": "No releases found."})

    def test_release_get_status_200(self):
        """Test get release existing"""
        _module = Module.objects.filter(slug="slug0").first()
        _module.status = 0
        _module.save()

        response = self.client.get(
            "/modules/api/v1/release/0.0.1",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        expected_result = {
            "version": "0.0.1",
            "releaseNotes": "release 0.0.1",
            "isSupported": False,
            "isDeprecated": False,
            "published": "1971-01-01",
            "unpublished": "1971-12-31",
            "deprecated": None,
            "created": str(response.data["created"]),
            "modified": str(response.data["modified"]),
            "modules": [
                {
                    "moduleSlug": "slug0",
                    "version": "1.2.3",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 0,
                },
                {
                    "moduleSlug": "slug1",
                    "version": "1.3.4",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
                {
                    "moduleSlug": "slug2",
                    "version": "1.30.4",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
                {
                    "moduleSlug": "slug3",
                    "version": "2.10.2",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
            ],
            "latestVersion": "0.1.1",
            "latestReleaseNotes": "release 0.1.1",
        }


        
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

    def test_release_get_latest_200(self):
        """Test get release existing"""
        response = self.client.get(
            "/modules/api/v1/release/latest",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        expected_result = {
            "version": "0.1.1",
            "releaseNotes": "release 0.1.1",
            "isSupported": False,
            "isDeprecated": False,
            "published": "1971-01-01",
            "unpublished": "1971-12-31",
            "deprecated": None,
            "created": str(response.data["created"]),
            "modified": str(response.data["modified"]),
            "modules": [
                {
                    "moduleSlug": "slug0",
                    "version": "1.2.20",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                },
            ],
            "latestVersion": "0.1.1",
            "latestReleaseNotes": "release 0.1.1",
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

    def test_release_post_200(self):
        """test release post missing keys"""
        data = {
            "version": "10.0.0",
            "releaseNotes": "test",
            "published": "1970-01-01",
            "unpublished": "1970-12-31",
            "deprecated": None,
            "modules": [{"moduleSlug": "slug0", "version": "1.2.3", "status": 0}],
        }
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "version": "10.0.0",
            "releaseNotes": "test",
            "isSupported": False,
            "isDeprecated": False,
            "published": "1970-01-01",
            "unpublished": "1970-12-31",
            "deprecated": None,
            "created": str(response.data["created"]),
            "modified": str(response.data["modified"]),
            "modules": [
                {
                    "moduleSlug": "slug0",
                    "version": "1.2.3",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                }
            ],
            "latestVersion": "10.0.0",
            "latestReleaseNotes": "test",
        }
        release = AppRelease.objects.filter(version="10.0.0").first()
        self.assertIsNotNone(release)
        self.assertListEqual(release.module_order, ["slug0"])


        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, expected_result)

        
        rms_list = ReleaseModuleStatus.objects.filter(app_release=release)
        self.assertEqual(len(rms_list), 1)

    def test_release_post_400_1(self):
        """test release pot missing keys"""
        data = {}
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, {"message": "Incorrect request body."})

    def test_release_post_400_2(self):
        """test release pot missing keys"""
        data = {
            "version": None,
            "releaseNotes": None,
            "published": None,
            "unpublished": None,
            "modules": None,
        }
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, {"message": "Incorrect request body."})

    def test_release_post_400_3(self):
        """test release pot missing keys"""
        data = {"version": "", "releaseNotes": None, "modules": []}
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, {"message": "Incorrect request body."})

    def test_release_post_409(self):
        """test release pot missing keys"""

        data = {
            "version": "0.0.0",
            "releaseNotes": "",
            "published": "",
            "unpublished": "",
            "deprecated": "",
            "modules": [],
        }
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertDictEqual(
            response.data, {"message": "Release version already exists."}
        )

    def test_release_post_404(self):
        """test release post missing keys"""
        data = {
            "version": "10.0.0",
            "releaseNotes": "",
            "published": "",
            "unpublished": "",
            "deprecated": "",
            "modules": [{"moduleSlug": "bogus", "version": "0.0.0", "status": 0}],
        }
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(
            response.data,
            {"message": "Module with slug 'bogus' and version '0.0.0' not found."},
        )

    def test_release_patch_200(self):
        """test release patch missing keys"""
        new_version = "0.0.1"
        new_release = AppRelease.objects.filter(version=new_version).first()
        new_release.published = None
        new_release.unpublished = None
        new_release.save()

        update_data = {
            "version": "10.0.0",
            "releaseNotes": "test",
            "isSupported": True,
            "isDeprecated": False,
            "published": "1970-01-01",
            "unpublished": "",
            "modules": [{"moduleSlug": "slug0", "version": "1.2.3", "status": 1}],
        }
        response = self.client.patch(
            f"/modules/api/v1/release/{new_version}",
            data=update_data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        expected_result = copy(update_data)
        expected_result["unpublished"] = None
        expected_result["deprecated"]=None
        expected_result["created"] = response.data["created"]
        expected_result["modified"] = response.data["modified"]
        expected_result["latestVersion"] = "10.0.0"
        expected_result["latestReleaseNotes"]="test"
        expected_result["modules"] = [
            {
                "moduleSlug": "slug0",
                "version": "1.2.3",
                "title": "title",
                "description": "description",
                "icon": "icon",
                "status": 1,
            }
        ]



        self.assertDictEqual(response.data, expected_result)

        modules_app_list = ReleaseModuleStatus.objects.filter(
            app_release__version=update_data["version"]
        )
        self.assertEqual(len(modules_app_list), 1)

        new_release.refresh_from_db()
        self.assertEqual(new_release.version, update_data["version"])
        self.assertEqual(new_release.release_notes, update_data["releaseNotes"])

    def test_release_patch_change_module_order(self):
        # Create new modules
        module_a = Module.objects.create(slug="module_a")
        module_b = Module.objects.create(slug="module_b")
        module_c = Module.objects.create(slug="module_c")
        # Create one version per module
        version_a = ModuleVersion.objects.create(
            module=module_a, version="1.0", title="foo", icon="foo", description="foo"
        )
        version_b = ModuleVersion.objects.create(
            module=module_b, version="1.0", title="foo", icon="foo", description="foo"
        )
        version_c = ModuleVersion.objects.create(
            module=module_c, version="1.0", title="foo", icon="foo", description="foo"
        )

        release_version = "1.0.0"
        release = AppRelease.objects.create(version=release_version, module_order=[])
        release.save()

        update_data = {
            "version": "10.0.0",
            "releaseNotes": "test",
            "published": "1970-01-01",
            "unpublished": "",
            "modules": [
                {
                    "moduleSlug": module_b.slug,
                    "version": version_b.version,
                    "status": 1,
                },
                {
                    "moduleSlug": module_c.slug,
                    "version": version_c.version,
                    "status": 1,
                },
                {
                    "moduleSlug": module_a.slug,
                    "version": version_a.version,
                    "status": 1,
                },
            ],
        }
        response = self.client.patch(
            f"/modules/api/v1/release/{release_version}",
            data=update_data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "moduleSlug": module_b.slug,
                "version": version_b.version,
                "title": "foo",
                "description": "foo",
                "icon": "foo",
                "status": 1,
            },
            {
                "moduleSlug": module_c.slug,
                "version": version_c.version,
                "title": "foo",
                "description": "foo",
                "icon": "foo",
                "status": 1,
            },
            {
                "moduleSlug": module_a.slug,
                "version": version_a.version,
                "title": "foo",
                "description": "foo",
                "icon": "foo",
                "status": 1,
            },
        ]

        self.assertListEqual(response.data["modules"], expected_result)

        # Expect same order of modules as in patch after refresh of object
        release.refresh_from_db()
        expected_module_order = [x["moduleSlug"] for x in update_data["modules"]]
        self.assertEqual(release.module_order, expected_module_order)

    def test_release_patch_403(self):
        """test release patch missing keys"""
        data = {
            "version": "10.0.0",
            "releaseNotes": "",
            "published": "",
            "unpublished": "",
            "modules": [{"moduleSlug": "bogus", "version": "0.0.0", "status": 0}],
        }
        response = self.client.patch(
            "/modules/api/v1/release/0.0.0",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(
            response.data, {"message": "Release version '0.0.0' already published."}
        )

    def test_release_patch_404(self):
        """test release patch missing keys"""
        data = {
            "version": "12.0.0",
            "releaseNotes": "",
            "published": "",
            "unpublished": "",
            "modules": [{"moduleSlug": "bogus", "version": "0.0.0", "status": 0}],
        }

        _release = {
            "version": "12.0.0",
            "release_notes": "test",
            "published": None,
            "unpublished": None,
            "module_order": ["slug0", "slug1"],
        }

        AppRelease.objects.create(**_release)
        response = self.client.patch(
            "/modules/api/v1/release/12.0.0",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(
            response.data,
            {"message": "Module with slug 'bogus' and version '0.0.0' not found."},
        )

    def test_release_delete_200(self):
        """test delete release 200"""
        release_version = "10.0.0"
        release = AppRelease.objects.create(version=release_version, module_order=[])

        response = self.client.delete(
            f"/modules/api/v1/release/{release_version}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, None)

        # Release should not exist anymore
        release = AppRelease.objects.filter(version=release_version).first()
        self.assertIsNone(release)

        # No related RMS objects should exist after delete of release
        rms = ReleaseModuleStatus.objects.filter(
            app_release__version=release_version
        ).first()
        self.assertIsNone(rms)

    def test_release_delete_403(self):
        """test delete release 403"""
        release_version = "0.0.1"
        response = self.client.delete(
            f"/modules/api/v1/release/{release_version}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {
            "message": f"Release version '{release_version}' is already published."
        }
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.data, expected_result)

        # Release should still exist
        release = AppRelease.objects.filter(version=release_version).first()
        self.assertIsNotNone(release)

    def test_release_delete_404(self):
        """test delete release 404"""
        release_version = "10.0.0"
        response = self.client.delete(
            f"/modules/api/v1/release/{release_version}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = {"message": f"Release version '{release_version}' not found."}
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.data, expected_result)

    def test_releases_get(self):
        """test releases"""
        response = self.client.get(
            "/modules/api/v1/releases",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "version": "0.1.1",
                "releaseNotes": "release 0.1.1",
                "published": "1971-01-01",
                "unpublished": "1971-12-31",
                "deprecated": None,
                "isSupported": False,
                "isDeprecated": False,
                "created": str(response.data[0]["created"]),
                "modified": str(response.data[0]["modified"]),
                "modules": [
                    {
                        "moduleSlug": "slug0",
                        "version": "1.2.20",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    },
                ],
                "latestVersion": "0.1.1",
                "latestReleaseNotes": "release 0.1.1",
            },
            {
                "version": "0.0.2",
                "releaseNotes": "release 0.0.2",
                "isSupported": False,
                "isDeprecated": False,
                "published": "1971-01-01",
                "unpublished": "1971-12-31",
                "deprecated": None,
                "created": str(response.data[1]["created"]),
                "modified": str(response.data[1]["modified"]),
                "modules": [
                    {
                        "moduleSlug": "slug0",
                        "version": "1.2.3",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    }
                ],
                "latestVersion": "0.1.1",
                "latestReleaseNotes": "release 0.1.1",
            },
            {
                "version": "0.0.1",
                "releaseNotes": "release 0.0.1",
                "isSupported": False,
                "isDeprecated": False,
                "published": "1971-01-01",
                "unpublished": "1971-12-31",
                "deprecated": None,
                "created": str(response.data[2]["created"]),
                "modified": str(response.data[2]["modified"]),
                "modules": [
                    {
                        "moduleSlug": "slug0",
                        "version": "1.2.3",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    },
                    {
                        "moduleSlug": "slug1",
                        "version": "1.3.4",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    },
                    {
                        "moduleSlug": "slug2",
                        "version": "1.30.4",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    },
                    {
                        "moduleSlug": "slug3",
                        "version": "2.10.2",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    },
                ],
                "latestVersion": "0.1.1",
                "latestReleaseNotes": "release 0.1.1",
            },
            {
                "version": "0.0.0",
                "releaseNotes": "release 0.0.0",
                "isSupported": False,
                "isDeprecated": False,
                "published": "1970-01-01",
                "unpublished": "1970-12-31",
                "deprecated": None,
                "created": str(response.data[3]["created"]),
                "modified": str(response.data[3]["modified"]),
                "modules": [
                    {
                        "moduleSlug": "slug4",
                        "version": "10.3.2",
                        "title": "title",
                        "description": "description",
                        "icon": "icon",
                        "status": 1,
                    },
                ],
                "latestVersion": "0.1.1",
                "latestReleaseNotes": "release 0.1.1",
            },
        ]

        for i, res_data in enumerate(response.data):
            expected_result_dict = expected_result[i]
            self.assertDictEqual(res_data, expected_result_dict)

    def test_get_deprecated_flag_for_release(self):
        """Test for release which is supported but deprecated. In practice this should not happend, this is just a test-case"""
        today = datetime.now()
        published_date = today - timedelta(days=10)
        deprecated_date = today - timedelta(days=1)
        """Create releases"""
        data_v14 = {
            "version": "14.0.0",
            "release_notes": "Release 14.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "module_order": [],
        }
        AppRelease.objects.create(**data_v14)

        data_v15 = {
            "version": "15.0.0",
            "release_notes": "Release 15.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": None,
            "module_order": [],
        }
        AppRelease.objects.create(**data_v15)

        response = response = self.client.get(
            "/modules/api/v1/release/14.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        expected_result = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "isSupported": True,
            "isDeprecated": True,
            "published": response.data["published"],
            "unpublished": None,
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "created": response.data["created"],
            "modified": response.data["modified"],
            "modules": [],
            "latestVersion": "15.0.0",
            "latestReleaseNotes": "Release 15.0.0",
        }

        self.assertDictEqual(response.data, expected_result)

    def test_get_unsupported_not_deprecated(self):
        """Test for a release which is supported but not deprecated"""
        today = datetime.now()
        published_date = today - timedelta(days=10)
        deprecated_date = today + timedelta(days=30)
        """Create releases"""
        data_v14 = {
            "version": "14.0.0",
            "release_notes": "Release 14.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "module_order": [],
        }
        AppRelease.objects.create(**data_v14)

        data_v15 = {
            "version": "15.0.0",
            "release_notes": "Release 15.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": None,
            "module_order": [],
        }
        AppRelease.objects.create(**data_v15)

        response = response = self.client.get(
            "/modules/api/v1/release/14.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        expected_result = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "isSupported": True,
            "isDeprecated": False,
            "published": response.data["published"],
            "deprecated": response.data["deprecated"],
            "unpublished": None,
            "created": response.data["created"],
            "modified": response.data["modified"],
            "modules": [],
            "latestVersion": "15.0.0",
            "latestReleaseNotes": "Release 15.0.0",
        }

        self.assertDictEqual(response.data, expected_result)

    def test_get_supported_flag_false_not_deprecated(self):
        """Test for a release which is not supported and not deprecated"""
        today = datetime.now()
        published_date = today - timedelta(days=10)
        unpublished_date = today - timedelta(days=5)
        """Create releases"""
        data_v14 = {
            "version": "14.0.0",
            "release_notes": "Release 14.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": unpublished_date.strftime(DEFAULT_DATE_FORMAT),
            "deprecated": None,
            "module_order": [],
        }
        AppRelease.objects.create(**data_v14)

        data_v15 = {
            "version": "15.0.0",
            "release_notes": "Release 15.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": None,
            "module_order": [],
        }
        AppRelease.objects.create(**data_v15)

        response = response = self.client.get(
            "/modules/api/v1/release/14.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        expected_result = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "isSupported": False,
            "isDeprecated": False,
            "published": response.data["published"],
            "unpublished": response.data["unpublished"],
            "deprecated": None,
            "created": response.data["created"],
            "modified": response.data["modified"],
            "modules": [],
            "latestVersion": "15.0.0",
            "latestReleaseNotes": "Release 15.0.0"
        }

        self.assertDictEqual(response.data, expected_result)

    def test_get_supported_false_and_deprecated_true(self):
        """Test for a release which is not supported and deprecated"""
        today = datetime.now()
        published_date = today - timedelta(days=10)
        unpublished_date = today - timedelta(days=5)
        deprecated_date = today - timedelta(days=3)
        """Create releases"""
        data_v14 = {
            "version": "14.0.0",
            "release_notes": "Release 14.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": unpublished_date.strftime(DEFAULT_DATE_FORMAT),
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "module_order": [],
        }
        AppRelease.objects.create(**data_v14)

        data_v15 = {
            "version": "15.0.0",
            "release_notes": "Release 15.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": None,
            "module_order": [],
        }
        AppRelease.objects.create(**data_v15)

        response = response = self.client.get(
            "/modules/api/v1/release/14.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        expected_result = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "isSupported": False,
            "isDeprecated": True,
            "published": response.data["published"],
            "unpublished": response.data["unpublished"],
            "deprecated": response.data["deprecated"],
            "created": response.data["created"],
            "modified": response.data["modified"],
            "modules": [],
            "latestVersion": "15.0.0",
            "latestReleaseNotes": "Release 15.0.0",
        }

        self.assertDictEqual(response.data, expected_result)

    def test_get_supported_and_none_deprecated(self):
        """Test for a release which is supported and not deprecated"""
        today = datetime.now()
        published_date = today - timedelta(days=10)
        unpublished_date = today + timedelta(days=25)
        deprecated_date = today + timedelta(days=30)
        """Create releases"""
        data_v14 = {
            "version": "14.0.0",
            "release_notes": "Release 14.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": unpublished_date.strftime(DEFAULT_DATE_FORMAT),
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "module_order": [],
        }
        AppRelease.objects.create(**data_v14)

        data_v15 = {
            "version": "15.0.0",
            "release_notes": "Release 15.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": None,
            "deprecated": None,
            "module_order": [],
        }
        AppRelease.objects.create(**data_v15)

        response = response = self.client.get(
            "/modules/api/v1/release/14.0.0",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        expected_result = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "isSupported": True,
            "isDeprecated": False,
            "published": response.data["published"],
            "unpublished": response.data["unpublished"],
            "deprecated": response.data["deprecated"],
            "created": response.data["created"],
            "modified": response.data["modified"],
            "modules": [],
            "latestVersion": "15.0.0",
            "latestReleaseNotes": "Release 15.0.0",
        }

        self.assertDictEqual(response.data, expected_result)

    def test_patch_with_deprecated_data(self):
        today = datetime.now()
        deprecated_date = today + timedelta(days=30)

        """test release patch missing keys"""
        new_version = "0.0.1"
        new_release = AppRelease.objects.filter(version=new_version).first()
        new_release.published = None
        new_release.unpublished = None
        new_release.deprecated_date = None
        new_release.save()

        update_data = {
            "version": "10.0.0",
            "releaseNotes": "test",
            "published": "1970-01-01",
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": "",
            "modules": [{"moduleSlug": "slug0", "version": "1.2.3", "status": 1}],
        }
        response = self.client.patch(
            f"/modules/api/v1/release/{new_version}",
            data=update_data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEquals(response.status_code, 200)

        # test for update
        release = AppRelease.objects.filter(version="10.0.0").first()
        self.assertIsNotNone(release)
        # has the deprecated date been updated?
        self.assertEquals(
            release.deprecated.strftime(DEFAULT_DATE_FORMAT),
            deprecated_date.strftime(DEFAULT_DATE_FORMAT),
        )

    def test_post_with_deprecated_date(self):
        today = datetime.now()
        published_date = today - timedelta(days=10)
        unpublished_date = today + timedelta(days=25)
        deprecated_date = today + timedelta(days=30)
        """Create release"""
        data = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "published": published_date.strftime(DEFAULT_DATE_FORMAT),
            "unpublished": unpublished_date.strftime(DEFAULT_DATE_FORMAT),
            "deprecated": deprecated_date.strftime(DEFAULT_DATE_FORMAT),
            "modules": [{"moduleSlug": "slug0", "version": "1.2.3", "status": 0}],
        }

        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        expected_result = {
            "version": "14.0.0",
            "releaseNotes": "Release 14.0.0",
            "isSupported": True,
            "isDeprecated": False,
            "published": data["published"],
            "unpublished": data["unpublished"],
            "deprecated": data["deprecated"],
            "created": str(response.data["created"]),
            "modified": str(response.data["modified"]),
            "modules": [
                {
                    "moduleSlug": "slug0",
                    "version": "1.2.3",
                    "title": "title",
                    "description": "description",
                    "icon": "icon",
                    "status": 1,
                }
            ],
            "latestVersion": "14.0.0",
            "latestReleaseNotes": "Release 14.0.0",
        }

        self.assertDictEqual(response.data, expected_result)
        # test voor existence
        release = AppRelease.objects.filter(version="14.0.0").first()
        self.assertIsNotNone(release)
        self.assertEquals(
            release.deprecated.strftime(DEFAULT_DATE_FORMAT),
            deprecated_date.strftime(DEFAULT_DATE_FORMAT),
        )
