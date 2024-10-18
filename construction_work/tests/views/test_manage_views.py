from django.conf import settings
from django.urls import reverse

from construction_work.models import Article, Project, ProjectManager, WarningMessage
from construction_work.tests import mock_data
from construction_work.tests.tools import apply_signing_key_patch, create_jwt_token
from core.tests import BaseAPITestCase


class BaseTestManageView(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.signing_key_patcher = apply_signing_key_patch(cls)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.signing_key_patcher.stop()

    def setUp(self) -> None:
        super().setUp()
        self.api_headers = {}

    def update_headers_with_editor_data(
        self, email="editor@amsterdam.nl", first_name=None, last_name=None
    ):
        jwt_token = create_jwt_token(
            groups=[settings.EDITOR_GROUP_ID],
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        self.api_headers["Accept"] = "application/json"
        self.api_headers["Authorization"] = jwt_token

    def update_headers_with_publisher_data(self, email="publisher@amsterdam.nl"):
        jwt_token = create_jwt_token(groups=[settings.PUBLISHER_GROUP_ID], email=email)
        self.api_headers["Accept"] = "application/json"
        self.api_headers["Authorization"] = jwt_token

    def update_headers_with_editor_publisher_data(
        self, publisher_email="publisher@amsterdam.nl"
    ):
        jwt_token = create_jwt_token(
            groups=[settings.EDITOR_GROUP_ID, settings.PUBLISHER_GROUP_ID],
            email=publisher_email,
        )
        self.api_headers["Accept"] = "application/json"
        self.api_headers["Authorization"] = jwt_token

    def create_project_and_publisher(self):
        project_data = mock_data.projects[0]
        project = Project.objects.create(**project_data)

        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )
        publisher.projects.add(project)
        publisher.save()

        return project, publisher


class TestManagePublisherCRUDViews(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()
        self.api_url_list_create = reverse(
            "construction-work:manage-publisher-list-create"
        )
        self.api_url_detail_str = (
            "construction-work:manage-publisher-read-update-delete"
        )
        self.api_url_assign_str = "construction-work:manage-publisher-assign-project"
        self.api_url_unassign_str = (
            "construction-work:manage-publisher-unassign-project"
        )

    def test_get_all_publishers(self):
        publisher1 = ProjectManager.objects.create(email="publisher1@amsterdam.nl")
        publisher2 = ProjectManager.objects.create(email="publisher2@amsterdam.nl")
        publisher3 = ProjectManager.objects.create(email="publisher3@amsterdam.nl")

        self.update_headers_with_editor_data()
        result = self.client.get(self.api_url_list_create, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)

        res_pub_emails = [x["email"] for x in result.data]
        self.assertListEqual(
            res_pub_emails, [publisher1.email, publisher2.email, publisher3.email]
        )

    def test_get_all_publishers_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.get(self.api_url_list_create, headers=self.api_headers)
        self.assertEqual(result.status_code, 403)

    def test_get_publisher(self):
        publisher = ProjectManager.objects.create(
            name="foobar",
            email="publisher@amsterdam.nl",
        )

        self.update_headers_with_editor_data()
        result = self.client.get(
            f"{reverse(self.api_url_detail_str, args=[publisher.pk])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        expected_data = {
            "id": publisher.pk,
            "name": publisher.name,
            "email": publisher.email,
            "projects": [],
        }
        self.assertDictEqual(result.data, expected_data)

    def test_get_self_as_publisher(self):
        publisher = ProjectManager.objects.create(
            name="foobar",
            email="publisher@amsterdam.nl",
        )
        self.update_headers_with_publisher_data(email=publisher.email)

        result = self.client.get(
            f"{reverse(self.api_url_detail_str, args=[publisher.pk])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        expected_data = {
            "id": publisher.pk,
            "name": publisher.name,
            "email": publisher.email,
            "projects": [],
        }
        self.assertDictEqual(result.data, expected_data)

    def test_get_other_publisher_as_publisher(self):
        publisher1 = ProjectManager.objects.create(
            name="foobar1",
            email="publisher1@amsterdam.nl",
        )

        publisher2 = ProjectManager.objects.create(
            name="foobar2",
            email="publisher2@amsterdam.nl",
        )

        self.update_headers_with_publisher_data(email=publisher1.email)
        result = self.client.get(
            f"{reverse(self.api_url_detail_str, args=[publisher2.pk])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_get_not_self_publisher_as_editor_publisher(self):
        editor_publisher = ProjectManager.objects.create(
            name="foobar",
            email="editor_publisher@amsterdam.nl",
        )
        publisher = ProjectManager.objects.create(
            name="foobar",
            email="publisher@amsterdam.nl",
        )

        self.update_headers_with_editor_publisher_data(
            publisher_email=editor_publisher.email
        )
        result = self.client.get(
            f"{reverse(self.api_url_detail_str, args=[publisher.pk])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

    def test_get_unknown_publisher(self):
        self.update_headers_with_editor_data()
        result = self.client.get(
            f"{reverse(self.api_url_detail_str, args=[9999])}", headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

    def test_create_publisher(self):
        publisher_data = {
            "name": "Foobar Publisher",
            "email": "publisher.foobar@amsterdam.nl",
        }

        self.update_headers_with_editor_data()
        result = self.client.post(
            self.api_url_list_create, data=publisher_data, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        new_publisher = ProjectManager.objects.filter(
            email=publisher_data["email"]
        ).first()
        self.assertIsNotNone(new_publisher)

    def test_create_publisher_as_publisher(self):
        self.update_headers_with_publisher_data()

        publisher_data = {
            "name": "Foobar Publisher",
        }
        result = self.client.post(
            self.api_url_list_create,
            data=publisher_data,
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 403)

        should_not_exist_publisher = ProjectManager.objects.filter(
            name=publisher_data["name"]
        ).first()
        self.assertIsNone(should_not_exist_publisher)

    def test_create_publisher_missing_data(self):
        self.update_headers_with_editor_data()

        publisher_data = {
            "name": "Foobar Publisher",
        }
        result = self.client.post(
            self.api_url_list_create,
            data=publisher_data,
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 400)

        should_not_exist_publisher = ProjectManager.objects.filter(
            name=publisher_data["name"]
        ).first()
        self.assertIsNone(should_not_exist_publisher)

        publisher_data = {
            "email": "publisher.foobar@amsterdam.nl",
        }
        result = self.client.post(
            self.api_url_list_create, data=publisher_data, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

        should_not_exist_publisher = ProjectManager.objects.filter(
            email=publisher_data["email"]
        ).first()
        self.assertIsNone(should_not_exist_publisher)

    def test_create_publisher_non_unique_email(self):
        email_address = "unique@amsterdam.nl"
        ProjectManager.objects.create(name="Some Publisher", email=email_address)

        publisher_data = {
            "name": "Other Publisher",
            "email": email_address,
        }

        self.update_headers_with_editor_data()
        result = self.client.post(
            self.api_url_list_create, data=publisher_data, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

        publisher_count = (
            ProjectManager.objects.filter(email=email_address).all().count()
        )
        self.assertEqual(publisher_count, 1)

    def test_update_publisher(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        updated_publisher_data = {
            "name": publisher.name,
            "email": "foobar@amsterdam.nl",
        }

        self.update_headers_with_editor_data()
        result = self.client.patch(
            f"{reverse(self.api_url_detail_str, args=[publisher.pk])}",
            data=updated_publisher_data,
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertEqual(publisher.name, updated_publisher_data["name"])
        self.assertEqual(publisher.email, updated_publisher_data["email"])

    def test_update_publisher_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.patch(
            f"{reverse(self.api_url_detail_str, args=[9999])}",
            data={},
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 403)

    def test_update_publisher_missing_data(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        updated_publisher_data = {
            # MISSING: "name": publisher.name,
            "email": "foobar@amsterdam.nl",
        }

        self.update_headers_with_editor_data()
        result = self.client.patch(
            f"{reverse(self.api_url_detail_str, args=[publisher.pk])}",
            data=updated_publisher_data,
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 400)

        # Object should not have been updated at all
        self.assertNotEqual(publisher.email, updated_publisher_data["email"])

    def test_update_publisher_that_does_not_exist(self):
        self.update_headers_with_editor_data()
        result = self.client.patch(
            f"{reverse(self.api_url_detail_str, args=[9999])}",
            data={},
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 404)

    def test_remove_publisher(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        self.update_headers_with_editor_data()
        result = self.client.delete(
            f"{reverse(self.api_url_detail_str, args=[publisher.pk])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        removed_publisher = ProjectManager.objects.filter(pk=publisher.pk).first()
        self.assertIsNone(removed_publisher)

    def test_remove_publisher_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.delete(
            f"{reverse(self.api_url_detail_str, args=[9999])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_remove_publisher_that_does_not_exist(self):
        self.update_headers_with_editor_data()
        result = self.client.delete(
            f"{reverse(self.api_url_detail_str, args=[9999])}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_assign_publisher_to_project(self):
        project = Project.objects.create(**mock_data.projects[0])
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        self.update_headers_with_editor_data()
        result = self.client.post(
            f"{reverse(self.api_url_assign_str, kwargs={'pk': publisher.pk})}",
            data={"project_id": project.pk},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertTrue(project in publisher.projects.all())

    def test_assign_publisher_to_project_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.post(
            f"{reverse(self.api_url_assign_str, kwargs={'pk': 9999})}",
            data={"project_id": 9999},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_test_assign_unknown_publisher_to_project(self):
        project = Project.objects.create(**mock_data.projects[0])

        self.update_headers_with_editor_data()
        result = self.client.post(
            f"{reverse(self.api_url_assign_str, kwargs={'pk': 9999})}",
            data={"project_id": project.pk},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_test_assign_publisher_to_unknown_project(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        self.update_headers_with_editor_data()
        result = self.client.post(
            f"{reverse(self.api_url_assign_str, kwargs={'pk': publisher.pk})}",
            data={"project_id": 9999},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_unassign_publisher_from_project(self):
        project, publisher = self.create_project_and_publisher()

        self.update_headers_with_editor_data()
        result = self.client.delete(
            f"{reverse(self.api_url_unassign_str, kwargs={'pk': publisher.pk, 'project_id': project.pk})}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertFalse(project in publisher.projects.all())

    def test_unassign_publisher_to_project_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.delete(
            f"{reverse(self.api_url_unassign_str, kwargs={'pk': 9999, 'project_id': 9999})}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_unassign_publisher_from_project_that_were_not_linked(self):
        project = Project.objects.create(**mock_data.projects[0])
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )
        self.update_headers_with_editor_data()
        result = self.client.delete(
            f"{reverse(self.api_url_unassign_str, kwargs={'pk': publisher.pk, 'project_id': project.pk})}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertFalse(project in publisher.projects.all())

    def test_unassign_unknown_publisher_from_project(self):
        project = Project.objects.create(**mock_data.projects[0])
        self.update_headers_with_editor_data()
        result = self.client.delete(
            f"{reverse(self.api_url_unassign_str, kwargs={'pk': 9999, 'project_id': project.pk})}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_unassign_publisher_from_unknown_project(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )
        self.update_headers_with_editor_data()
        result = self.client.delete(
            f"{reverse(self.api_url_unassign_str, kwargs={'pk': publisher.pk, 'project_id': 9999})}",
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)


class TestManageProjectListView(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()

        self.api_url = reverse("construction-work:manage-project-list")

    def assert_get_all_projects(self):
        project1 = Project.objects.create(**mock_data.projects[0])
        project2 = Project.objects.create(**mock_data.projects[1])

        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)

        project_ids = [x["id"] for x in result.data]
        self.assertListEqual(project_ids, [project1.pk, project2.pk])

    def test_get_all_projects_as_editor(self):
        self.update_headers_with_editor_data()

        self.assert_get_all_projects()

    def test_get_all_projects_as_editor_publisher(self):
        self.update_headers_with_editor_publisher_data()

        self.assert_get_all_projects()

    def test_project_article_warning_count(self):
        self.update_headers_with_editor_data()

        project = Project.objects.create(**mock_data.projects[0])

        warning_data = mock_data.warning_message.copy()
        warning_data["project_id"] = project.pk

        warnings = [
            WarningMessage.objects.create(**warning_data),
            WarningMessage.objects.create(**warning_data),
            WarningMessage.objects.create(**warning_data),
        ]

        for article_data in mock_data.articles:
            article = Article.objects.create(**article_data)
            article.projects.add(project)

        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)

        relevant_project = next(
            (d for d in result.data if d.get("id") == project.pk), None
        )

        self.assertEqual(relevant_project["warning_count"], len(warnings))
        self.assertEqual(relevant_project["article_count"], len(mock_data.articles))

    def test_get_projects_related_to_publisher(self):
        publisher = ProjectManager.objects.create(email="publisher@amsterdam.nl")

        project_related = Project.objects.create(**mock_data.projects[0])

        publisher.projects.add(project_related)
        publisher.save()

        project_unrelated = Project.objects.create(**mock_data.projects[1])

        self.update_headers_with_publisher_data(publisher.email)

        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)

        project_ids = [x["id"] for x in result.data]
        self.assertListEqual(project_ids, [project_related.pk])
        self.assertTrue(project_unrelated.pk not in project_ids)

    def test_get_projects_with_unkown_publisher(self):
        self.update_headers_with_publisher_data("foobar@amsterdam.nl")

        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 403)
