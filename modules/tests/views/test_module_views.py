from modules.models import Module, ModuleVersion
from modules.tests.setup import TestCaseWithAuth


class TestModuleViews(TestCaseWithAuth):
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

        response = self.client.get(
            f"/modules/api/v1/module/{module_slug}", HTTP_AUTHORIZATION=self.jwt_token
        )
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
            "/modules/api/v1/module/bogus", HTTP_AUTHORIZATION=self.jwt_token
        )
        error_code = "MODULE_NOT_FOUND"
        self.assertContains(response, error_code, status_code=404)

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
        expected_result = {"slug": "new", "status": 1}
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

        expected_result = {"slug": slug, "status": updated_status}
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
        self.assertContains(response, "NO_INPUT_DATA", status_code=400)

    def test_module_patch_module_not_found(self):
        """test patch but module not found"""
        data = {"status": 1}
        response = self.client.patch(
            "/modules/api/v1/module/bogus",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        error_code = "MODULE_NOT_FOUND"
        self.assertContains(response, error_code, status_code=404)

    def test_module_delete_with_active_module_version(self):
        """test delete model in use"""
        slug = "slug0"
        response = self.client.delete(
            f"/modules/api/v1/module/{slug}",
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        error_code = "MODULE_PROTECTED"
        self.assertContains(response, error_code, status_code=403)

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
            HTTP_AUTHORIZATION=self.jwt_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
