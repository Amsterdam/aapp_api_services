from modules.models import Module, ModuleVersion
from modules.tests.setup import TestCaseWithAuth


class TestModuleVersionViews(TestCaseWithAuth):
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
            f"/modules/api/v1/module/{module_slug}/version/",
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
            "/modules/api/v1/module/string/version/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

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
            "/modules/api/v1/module/slug0/version/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_ALREADY_EXISTS"
        self.assertContains(response, expected_result, status_code=409)

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
            "/modules/api/v1/module/bogus/version/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

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
            "/modules/api/v1/module/slug0/version/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "INCORRECT_VERSION"
        self.assertContains(response, expected_result, status_code=400)

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
            "/modules/api/v1/module/slug0/version/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "INCORRECT_VERSION"
        self.assertContains(response, expected_result, status_code=400)

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
            "/modules/api/v1/module/slug10/version/9.9.9/",
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
            "/modules/api/v1/module/slug0/version/1.2.3/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "INPUT_DATA"
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, expected_result, status_code=400)

    def test_module_slug_version_patch_not_found(self):
        """test incorrect request body"""
        data = {}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/3.4.5/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

    def test_module_slug_version_patch_incorrect_version(self):
        """test incorrect request body"""
        data = {"version": "3.4.5a"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "INCORRECT_VERSION"
        self.assertContains(response, expected_result, status_code=400)

    def test_module_slug_version_patch_in_use_1(self):
        """test incorrect request body"""
        data = {"version": "10.11.12"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_PROTECTED"
        self.assertContains(response, expected_result, status_code=403)

    def test_module_slug_version_patch_in_use_2(self):
        """test incorrect request body"""
        data = {"description": "test"}
        response = self.client.patch(
            "/modules/api/v1/module/slug0/version/1.2.3/",
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
            "/modules/api/v1/module/slug0/version/9.9.9/",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_PROTECTED"
        self.assertContains(response, expected_result, status_code=403)

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
            f"/modules/api/v1/module/{slug}/version/{version}/",
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
            "/modules/api/v1/module/slug0/version/4.5.6/",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)

    def test_module_slug_version_delete_in_use(self):
        """test incorrect request body"""
        response = self.client.delete(
            "/modules/api/v1/module/slug0/version/1.2.3/",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        expected_result = "MODULE_PROTECTED"
        self.assertContains(response, expected_result, status_code=403)

    def test_module_version_get_exist(self):
        """get module by slug and version (exists)"""
        response = self.client.get(
            "/modules/api/v1/module/slug0/version/1.2.3/",
            HTTP_AUTHORIZATION=self.jwt_token,
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
            "/modules/api/v1/module/bogus0/version/0.0.0/",
            HTTP_AUTHORIZATION=self.jwt_token,
        )
        expected_result = "MODULE_NOT_FOUND"
        self.assertContains(response, expected_result, status_code=404)
