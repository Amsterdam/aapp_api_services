import json
import os
import pathlib
from random import randint
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from construction_work.models.article_models import Article
from construction_work.models.manage_models import (
    Device,
    Image,
    ProjectManager,
    WarningImage,
    WarningMessage,
)
from construction_work.models.project_models import Project
from construction_work.tests import mock_data
from construction_work.utils.patch_utils import (
    MockNotificationResponse,
    apply_signing_key_patch,
    create_jwt_token,
)

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]


class BaseTestManageView(APITestCase):
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


class TestPublisherListCreateView(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()
        self.api_url = reverse("construction-work:manage-publisher-list-create")

    def test_get_all_publishers(self):
        publisher1 = ProjectManager.objects.create(email="publisher1@amsterdam.nl")
        publisher2 = ProjectManager.objects.create(email="publisher2@amsterdam.nl")
        publisher3 = ProjectManager.objects.create(email="publisher3@amsterdam.nl")

        self.update_headers_with_editor_data()
        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)

        res_pub_emails = [x["email"] for x in result.data]
        self.assertListEqual(
            res_pub_emails, [publisher1.email, publisher2.email, publisher3.email]
        )

    def test_get_all_publishers_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 403)

    def test_create_publisher(self):
        publisher_data = {
            "name": "Foobar Publisher",
            "email": "publisher.foobar@amsterdam.nl",
        }

        self.update_headers_with_editor_data()
        result = self.client.post(
            self.api_url, data=publisher_data, headers=self.api_headers
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
            self.api_url,
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
            self.api_url,
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
            self.api_url, data=publisher_data, headers=self.api_headers
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
            self.api_url, data=publisher_data, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

        publisher_count = (
            ProjectManager.objects.filter(email=email_address).all().count()
        )
        self.assertEqual(publisher_count, 1)


class TestPublisherDetailView(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()
        self.api_url_str = "construction-work:manage-publisher-read-update-delete"

    def test_get_publisher(self):
        publisher = ProjectManager.objects.create(
            name="foobar",
            email="publisher@amsterdam.nl",
        )

        self.update_headers_with_editor_data()
        result = self.client.get(
            reverse(self.api_url_str, args=[publisher.pk]),
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
            reverse(self.api_url_str, args=[publisher.pk]),
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
            reverse(self.api_url_str, args=[publisher2.pk]),
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
            reverse(self.api_url_str, args=[publisher.pk]),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

    def test_get_unknown_publisher(self):
        self.update_headers_with_editor_data()
        result = self.client.get(
            reverse(self.api_url_str, args=[9999]), headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

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
            reverse(self.api_url_str, args=[publisher.pk]),
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
            reverse(self.api_url_str, args=[9999]),
            data={},
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 403)

    def test_update_publisher_that_does_not_exist(self):
        self.update_headers_with_editor_data()
        result = self.client.patch(
            reverse(self.api_url_str, args=[9999]),
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
            reverse(self.api_url_str, args=[publisher.pk]),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        removed_publisher = ProjectManager.objects.filter(pk=publisher.pk).first()
        self.assertIsNone(removed_publisher)

    def test_remove_publisher_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.delete(
            reverse(self.api_url_str, args=[9999]),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_remove_publisher_that_does_not_exist(self):
        self.update_headers_with_editor_data()
        result = self.client.delete(
            reverse(self.api_url_str, args=[9999]),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)


class TestPublisherAssignProjectView(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()
        self.api_url_str = "construction-work:manage-publisher-assign-project"

    def test_assign_publisher_to_project(self):
        project = Project.objects.create(**mock_data.projects[0])
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        self.update_headers_with_editor_data()
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": publisher.pk}),
            data={"project_id": project.pk},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertTrue(project in publisher.projects.all())

    def test_assign_publisher_to_project_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": 9999}),
            data={"project_id": 9999},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_assign_unknown_publisher_to_project(self):
        project = Project.objects.create(**mock_data.projects[0])

        self.update_headers_with_editor_data()
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": 9999}),
            data={"project_id": project.pk},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_assign_publisher_to_unknown_project(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )

        self.update_headers_with_editor_data()
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": publisher.pk}),
            data={"project_id": 9999},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)


class TestPublisherUnassignProjectView(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()
        self.api_url_str = "construction-work:manage-publisher-unassign-project"

    def test_unassign_publisher_from_project(self):
        project, publisher = self.create_project_and_publisher()

        self.update_headers_with_editor_data()
        result = self.client.delete(
            reverse(
                self.api_url_str,
                kwargs={"pk": publisher.pk, "project_id": project.pk},
            ),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertFalse(project in publisher.projects.all())

    def test_unassign_publisher_to_project_as_publisher(self):
        self.update_headers_with_publisher_data()
        result = self.client.delete(
            reverse(self.api_url_str, kwargs={"pk": 9999, "project_id": 9999}),
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
            reverse(
                self.api_url_str,
                kwargs={"pk": publisher.pk, "project_id": project.pk},
            ),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        publisher.refresh_from_db()
        self.assertFalse(project in publisher.projects.all())

    def test_unassign_unknown_publisher_from_project(self):
        project = Project.objects.create(**mock_data.projects[0])
        self.update_headers_with_editor_data()
        result = self.client.delete(
            reverse(self.api_url_str, kwargs={"pk": 9999, "project_id": project.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_unassign_publisher_from_unknown_project(self):
        publisher = ProjectManager.objects.create(
            name="foobar", email="publisher@amsterdam.nl"
        )
        self.update_headers_with_editor_data()
        result = self.client.delete(
            reverse(
                self.api_url_str,
                kwargs={"pk": publisher.pk, "project_id": 9999},
            ),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)


class TestProjectListForManageView(BaseTestManageView):
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

    def test_get_projects_with_related_publishers_name_and_emails(self):
        project = Project.objects.create(**mock_data.projects[0])
        manager1 = ProjectManager.objects.create(
            name="Publisher 1", email="publisher1@amsterdam.nl"
        )
        manager1.projects.add(project)
        manager2 = ProjectManager.objects.create(
            name="Publisher 2", email="publisher2@amsterdam.nl"
        )
        manager2.projects.add(project)

        self.update_headers_with_editor_data()
        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)

        project_data = next((d for d in result.data if d.get("id") == project.pk), None)
        self.assertEqual(
            project_data["publishers"],
            [
                {"name": manager1.name, "email": manager1.email},
                {"name": manager2.name, "email": manager2.email},
            ],
        )


class TestProjectDetailsForManageView(BaseTestManageView):
    def setUp(self) -> None:
        super().setUp()

        self.api_url_str = "construction-work:manage-project-details"

    def test_get_project_details_success(self):
        self.update_headers_with_editor_data()

        project = Project.objects.create(**mock_data.projects[0])

        manager1 = ProjectManager.objects.create(email="editor@amsterdam.nl")
        manager1.projects.add(project)
        manager1.save()

        manager2 = ProjectManager.objects.create(email="publisher@amsterdam.nl")
        manager2.projects.add(project)
        manager2.save()

        warning_data = mock_data.warning_message.copy()
        warning_data["project_id"] = project.pk

        warning1 = WarningMessage.objects.create(**warning_data)
        warning2 = WarningMessage.objects.create(**warning_data)

        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        manager_emails = [x.get("email") for x in result.data.get("publishers")]
        self.assertListEqual(manager_emails, [manager1.email, manager2.email])

        warning_ids = [x.get("id") for x in result.data.get("warnings")]
        self.assertListEqual(warning_ids, [warning1.pk, warning2.pk])

    def test_project_id_does_not_exist(self):
        self.update_headers_with_editor_data()

        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": 9999}), headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

    def test_get_assigned_project_as_publisher(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

    def test_get_unassigned_project_as_publisher(self):
        project_data = mock_data.projects[0]
        project = Project.objects.create(**project_data)

        self.update_headers_with_publisher_data()

        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)


class TestWarningMessageCRUDBaseView(BaseTestManageView):
    def create_warning_image(self, warning=None):
        new_warning_image = WarningImage(warning=warning, image_set_id=randint(1, 1000))
        new_warning_image.save()
        for i in range(3):
            new_warning_image.image_set.create(
                image=f"image-{i}.png",
                description="new image description",
                width=10,
                height=10,
            )
        return new_warning_image


class TestWarningMessageCreateView(TestWarningMessageCRUDBaseView):
    def setUp(self) -> None:
        super().setUp()

        self.api_url_str = "construction-work:manage-warning-create"

    @patch(
        "construction_work.serializers.manage_serializers.WarningMessageCreateUpdateSerializer.construct_warning_image"
    )
    def test_create_warning_with_image_without_push_notification(
        self, mock_construct_image
    ):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        new_warning_image = self.create_warning_image()
        mock_construct_image.return_value = new_warning_image

        request_data = {
            "title": "title of new warning",
            "body": "body of new warning",
            "warning_image": {
                "id": new_warning_image.image_set_id,
                "description": "this should be ignored",
            },
            "send_push_notification": False,
        }
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=json.dumps(request_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)

        self.assertFalse(result.data.get("push_ok"))
        self.assertFalse(result.data.get("push_message"))

        new_warning_id = result.data.get("id")
        new_warning = WarningMessage.objects.filter(pk=new_warning_id).first()
        self.assertIsNotNone(new_warning)

        new_warning_image = WarningImage.objects.filter(warning=new_warning).first()
        self.assertIsNotNone(new_warning_image)

        image_count = WarningImage.objects.filter(warning=new_warning).all().count()
        self.assertEqual(image_count, 1)

        get_waring_url = reverse("construction-work:get-warning")
        query_params = {"id": new_warning_id}
        get_url_with_params = f"{get_waring_url}?{urlencode(query_params)}"

        api_keys = settings.API_KEYS.split(",")
        get_headers = {settings.API_KEY_HEADER: api_keys[0]}
        get_response = self.client.get(
            get_url_with_params,
            headers=get_headers,
        )
        self.assertEqual(get_response.status_code, 200)

    def test_create_warning_without_image(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        request_data = {
            "title": "title of new warning",
            "body": "body of new warning",
            "send_push_notification": False,
        }
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=json.dumps(request_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)

        new_warning_id = result.data.get("id")
        new_warning = WarningMessage.objects.filter(pk=new_warning_id).first()
        self.assertIsNotNone(new_warning)

        new_warning_image = WarningImage.objects.filter(warning=new_warning).first()
        self.assertIsNone(new_warning_image)

    def test_create_warning_as_editor(self):
        """
        When editor creates warning, they are automatically linked
        as project manager to related project.
        """
        project_data = mock_data.projects[0].copy()
        project = Project.objects.create(**project_data)

        editor_email = "editor@amsterdam.nl"
        editor_first_name = "Foo"
        editor_last_name = "Bar"
        self.update_headers_with_editor_data(
            email=editor_email, first_name=editor_first_name, last_name=editor_last_name
        )
        request_data = {
            "title": "title of new warning",
            "body": "body of new warning",
            "send_push_notification": False,
        }

        # Check that editor is not yet known as project manager
        project_manager = ProjectManager.objects.filter(email=editor_email).first()
        self.assertIsNone(project_manager)

        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=json.dumps(request_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)

        # Test if warning was created
        new_warning_id = result.data.get("id")
        new_warning = WarningMessage.objects.filter(pk=new_warning_id).first()
        self.assertIsNotNone(new_warning)

        # Test if editor is now a project manager and linked to project
        project_manager = ProjectManager.objects.filter(email=editor_email).first()
        self.assertIsNotNone(project_manager)
        self.assertEqual(
            project_manager.name, f"{editor_first_name} {editor_last_name}"
        )

        # Test if editor is linked to project that warning was created for
        self.assertTrue(project in project_manager.projects.all())

    def test_create_warning_as_unknown_publisher(self):
        self.update_headers_with_publisher_data("foobar@amsterdam.nl")
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": 1}),
            data={},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_create_warning_for_unknown_project(self):
        _, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        unknown_project_id = 9999
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": unknown_project_id}),
            data={},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 404)

    def test_publisher_not_related_to_project(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        # Decouple publisher from project
        publisher.projects.remove(project)
        publisher.save()

        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data={},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_incorrect_boolean_value(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        request_data = {
            "title": "title of new warning",
            "body": "body of new warning",
            "send_push_notification": "foobar",
        }
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=request_data,
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 400)

    def test_create_warning_missing_data(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        request_data = {
            "title": "title of new warning",
            # missing body value
        }
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=request_data,
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 400)

        request_data = {
            # missing title value
            "body": "body of new warning",
        }
        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=request_data,
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 400)

    @patch(
        "construction_work.services.notification.requests.post",
    )
    def test_create_warning_with_push_notification(self, post_notification):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        request_data = {
            "title": "title of new warning",
            "body": "body of new warning",
            "send_push_notification": True,
        }

        # Add follower of project, so notification will be sent
        device_data = mock_data.devices[0].copy()
        new_device = Device.objects.create(**device_data)
        new_device.followed_projects.add(project)

        post_notification.return_value = MockNotificationResponse(
            title=request_data["title"], body=request_data["body"]
        )

        result = self.client.post(
            reverse(self.api_url_str, kwargs={"pk": project.pk}),
            data=request_data,
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.data.get("push_message"))

        new_warning_id = result.data.get("id")
        new_warning = WarningMessage.objects.filter(pk=new_warning_id).first()
        self.assertIsNotNone(new_warning)
        self.assertTrue(new_warning.notification_sent)


class TestWarningMessageDetailView(TestWarningMessageCRUDBaseView):
    def setUp(self) -> None:
        super().setUp()
        self.api_url_str = "construction-work:manage-warning-read-update-delete"

    def create_warning(self, project, publisher):
        warning_data = mock_data.warning_message.copy()
        warning_data["project"] = project
        warning_data["project_manager"] = publisher
        return WarningMessage.objects.create(**warning_data)

    def test_get_warning(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        warning = self.create_warning(project, publisher)
        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

    def test_get_warning_with_images(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        warning = self.create_warning(project, publisher)
        self.create_warning_image(warning)

        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        image_in_result = result.data["images"][0]
        self.assertIsNotNone(image_in_result.get("alternativeText"))
        self.assertIsNotNone(image_in_result["sources"][0].get("uri"))

    def test_get_unknown_warning(self):
        _, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        result = self.client.get(
            reverse(self.api_url_str, kwargs={"pk": 9999}), headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

    def assert_update_warning_successfully(self, project, publisher):
        warning = self.create_warning(project, publisher)
        new_data = {
            "title": "new warning title",
            "body": "new warning body",
            "send_push_notification": False,
        }
        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            data=json.dumps(new_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)
        # Test if values returned contain updated data
        self.assertEqual(result.data["title"], new_data["title"])
        self.assertEqual(result.data["body"], new_data["body"])

        # Test if object was actually updated in database
        warning.refresh_from_db()
        self.assertEqual(warning.title, new_data["title"])
        self.assertEqual(warning.body, new_data["body"])

    def test_update_warning_title_and_body_success(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        self.assert_update_warning_successfully(project, publisher)

    def test_update_unknown_warning(self):
        _, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": 9999}), headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

    def test_update_warning_unrelated_to_publisher(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        # Remove relation to project from publisher
        publisher.projects.remove(project)

        warning = self.create_warning(project, publisher)
        new_data = {
            "title": "new warning title",
            "body": "new warning body",
            "send_push_notification": False,
        }
        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            data=new_data,
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 403)

    def test_update_warning_by_editor(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_editor_data()

        self.assert_update_warning_successfully(project, publisher)

    def test_update_warning_delete_image(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        # Setup existing warning message with image
        warning = self.create_warning(project, publisher)
        original_warning_image = self.create_warning_image(warning)

        # PATCH warning message
        new_data = {
            "title": warning.title,
            "body": warning.body,
            "send_push_notification": False,
        }
        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            data=json.dumps(new_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)

        # Check if original warning image does not point to the warning anymore
        original_warning_image = WarningImage.objects.get(pk=original_warning_image.pk)
        self.assertEquals(original_warning_image.warning, None)
        # and no image is linked to the warning
        new_warning_image = WarningImage.objects.filter(warning=warning).first()
        self.assertIsNone(new_warning_image)

    @patch(
        "construction_work.serializers.manage_serializers.WarningMessageCreateUpdateSerializer.construct_warning_image"
    )
    def test_update_warning_replace_image(self, mock_construct_image):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        # Setup existing warning message with image
        warning = self.create_warning(project, publisher)
        original_warning_image = self.create_warning_image(warning)
        new_warning_image = self.create_warning_image()

        mock_construct_image.return_value = new_warning_image

        new_data = {
            "title": warning.title,
            "body": warning.body,
            "warning_image": {
                "id": new_warning_image.image_set_id,
                "description": "new image description",
            },
            "send_push_notification": False,
        }

        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            data=json.dumps(new_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)

        # Check if original warning image was removed,
        original_warning_image = WarningImage.objects.filter(
            pk=original_warning_image.pk
        ).first()
        self.assertEquals(original_warning_image.warning, None)
        # and new image is created
        new_warning_image = WarningImage.objects.filter(warning=warning).first()
        self.assertIsNotNone(new_warning_image)
        # and description is updated
        first_image = Image.objects.get(pk=new_warning_image.image_set.first().pk)
        self.assertEqual(first_image.description, "new image description")
        # and a warning only has a single image
        image_count = WarningImage.objects.filter(warning=warning).all().count()
        self.assertEqual(image_count, 1)

    @patch(
        "construction_work.services.notification.requests.post",
    )
    def test_update_warning_send_push_ok(self, post_notification):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        # Add follower of project, so notification will be sent
        device_data = mock_data.devices[0].copy()
        new_device = Device.objects.create(**device_data)
        new_device.followed_projects.add(project)

        warning = self.create_warning(project, publisher)
        new_data = {
            "title": warning.title,
            "body": warning.body,
            "send_push_notification": True,
        }

        post_notification.return_value = MockNotificationResponse(
            warning_id=warning.pk, title=new_data["title"], body=new_data["body"]
        )

        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            data=json.dumps(new_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.data.get("push_message"))

        warning.refresh_from_db()
        self.assertTrue(warning.notification_sent)

    def test_update_warning_send_notification_not_allowed(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        warning = self.create_warning(project, publisher)
        warning.notification_sent = True
        warning.save()

        new_data = {
            "title": warning.title,
            "body": warning.body,
            "send_push_notification": True,
        }
        result = self.client.patch(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            data=json.dumps(new_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.data.get("push_code"))
        self.assertIsNone(result.data.get("push_message"))

    def assert_remove_warning_successfully(self, project, publisher):
        warning = self.create_warning(project, publisher)
        result = self.client.delete(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        deleted_warning = WarningMessage.objects.filter(pk=warning.pk).first()
        self.assertIsNone(deleted_warning)

    def test_remove_warning_success(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        self.assert_remove_warning_successfully(project, publisher)

    def test_remove_unkown_warning(self):
        _, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        result = self.client.delete(
            reverse(self.api_url_str, kwargs={"pk": 9999}), headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

    def test_remove_warning_unrelated_to_publisher(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

        # Remove relation to project from publisher
        publisher.projects.remove(project)

        warning = self.create_warning(project, publisher)
        result = self.client.delete(
            reverse(self.api_url_str, kwargs={"pk": warning.pk}),
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 403)

    def test_remove_warning_by_editor(self):
        project, publisher = self.create_project_and_publisher()
        self.update_headers_with_editor_data()

        self.assert_remove_warning_successfully(project, publisher)


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
)
class TestImageUploadView(TestWarningMessageCRUDBaseView):
    def setUp(self):
        super().setUp()
        self.api_url = reverse("construction-work:image-upload")
        file_path = "construction_work/tests/image_data/small_image.png"
        file = open(os.path.join(ROOT_DIR, file_path), "rb")
        self.valid_image_data = {"image": file}
        self.invalid_image_data = {"image": ""}
        _, publisher = self.create_project_and_publisher()
        self.update_headers_with_publisher_data(publisher.email)

    @patch("core.services.image_set.requests.post")
    def test_upload_image_success(self, mock_post):
        """
        Test that a POST request with valid data successfully uploads an image.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123}
        mock_post.return_value = mock_response

        response = self.client.post(
            self.api_url,
            headers=self.api_headers,
            data=self.valid_image_data,
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("warning_image_id", response.data)

    def test_upload_image_method_not_allowed(self):
        """
        Test that a GET request to the endpoint returns a 405 Method Not Allowed.
        """
        response = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(response.status_code, 405)

    def test_upload_image_missing_fields(self):
        """
        Test that a POST request with missing required fields returns a 400 Bad Request.
        """
        response = self.client.post(
            self.api_url, headers=self.api_headers, data={}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
