from copy import copy
from datetime import datetime, timedelta

from django.utils import timezone

from modules.models import AppRelease, Module, ModuleVersion, ReleaseModuleStatus
from modules.tests.setup import TestCaseWithAuth

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class TestReleaseViews(TestCaseWithAuth):
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
        self.assertContains(response, "does not exist", status_code=404)

    def test_release_get_404_2(self):
        """Test get release not existing"""
        AppRelease.objects.filter().delete()
        response = self.client.get(
            "/modules/api/v1/release/latest",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
            accept="application/json",
        )
        expected_result = "RELEASE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

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
        expected_result = "INPUT_DATA"
        self.assertContains(response, expected_result, status_code=400)

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
        expected_result = "INPUT_DATA"
        self.assertContains(response, expected_result, status_code=400)

    def test_release_post_400_3(self):
        """test release pot missing keys"""
        data = {"version": "", "releaseNotes": None, "modules": []}
        response = self.client.post(
            "/modules/api/v1/release",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "INPUT_DATA"
        self.assertContains(response, expected_result, status_code=400)

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

        expected_result = "MODULE_ALREADY_EXISTS"
        self.assertContains(response, expected_result, status_code=409)

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
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

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
        expected_result["deprecated"] = None
        expected_result["created"] = response.data["created"]
        expected_result["modified"] = response.data["modified"]
        expected_result["latestVersion"] = "10.0.0"
        expected_result["latestReleaseNotes"] = "test"
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
        expected_result = "RELEASE_PROTECTED"
        self.assertContains(response, expected_result, status_code=403)

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
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

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
        expected_result = "RELEASE_PROTECTED"
        self.assertContains(response, expected_result, status_code=403)

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
        expected_result = f"Release version '{release_version}' does not exist."
        self.assertContains(response, expected_result, status_code=404)

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
        today = timezone.now().date()
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

        response = self.client.get(
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
            "latestReleaseNotes": "Release 15.0.0",
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

        response = self.client.get(
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
        today = timezone.now().date()
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
        release_deprecated = timezone.make_naive(release.deprecated).date()
        # has the deprecated date been updated?
        self.assertEquals(
            release_deprecated,
            deprecated_date,
        )

    def test_post_with_deprecated_date(self):
        today = timezone.now().date()
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
        release_deprecated = timezone.make_naive(release.deprecated).date()
        self.assertEquals(
            release_deprecated,
            deprecated_date,
        )
