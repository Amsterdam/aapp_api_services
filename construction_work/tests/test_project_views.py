import json

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.urls import reverse
from freezegun import freeze_time

from construction_work.models import Article, Device, Project, WarningMessage
from construction_work.tests import mock_data
from core.tests import BaseAPITestCase


def get_header_name(header_name: str) -> str:
    return f"HTTP_{header_name.upper().replace('-', '_')}"


class BaseTestApi(BaseAPITestCase):
    """Abstract base class for API tests"""

    def setUp(self):
        super().setUp()

        self.maxDiff = None

        # Create needed database extensions
        connection = connections[DEFAULT_DB_ALIAS]
        cursor = connection.cursor()
        cursor.execute("CREATE EXTENSION pg_trgm")
        cursor.execute("CREATE EXTENSION unaccent")

    def create_project_and_article(self, project_foreign_id, pub_date):
        """Create project and article"""
        project_data = mock_data.projects[0]
        project_data["foreign_id"] = project_foreign_id
        project = Project.objects.create(**project_data)

        article_data = mock_data.articles[0]
        article_data["foreign_id"] = project_foreign_id + 1
        article_data["publication_date"] = pub_date
        article = Article.objects.create(**article_data)
        article.projects.add(project)

        return project, article

    def create_project_and_warning(self, project_foreign_id, pub_date):
        """Create project and warning"""
        project_data = mock_data.projects[0]
        project_data["foreign_id"] = project_foreign_id
        project = Project.objects.create(**project_data)

        warning_data = mock_data.warning_message
        warning_data["project"] = project
        warning = WarningMessage.objects.create(**warning_data)
        warning.publication_date = pub_date
        warning.save()

        return project, warning

    def add_article_to_project(self, project: Project, foreign_id, pub_date):
        """Add article to projects"""
        article_data = mock_data.articles[0]
        article_data["foreign_id"] = foreign_id
        article_data["publication_date"] = pub_date
        article = Article.objects.create(**article_data)
        article.projects.add(project)
        return article

    def add_warning_to_project(self, project: Project, pub_date):
        """Add warning to project"""
        warning_data = mock_data.warning_message
        warning_data["project"] = project
        warning = WarningMessage.objects.create(**warning_data)
        warning.publication_date = pub_date
        warning.save()

        return warning


class TestProjectListView(BaseTestApi):
    """Tests for getting all projects via API"""

    def setUp(self):
        super().setUp()
        self.api_url = reverse("projects-list")

    def tearDown(self) -> None:
        Project.objects.all().delete()
        Article.objects.all().delete()
        Device.objects.all().delete()
        super().tearDown()

    def test_method_not_allowed(self):
        self.api_headers[get_header_name(settings.HEADER_DEVICE_ID)] = 1
        response = self.client.post(self.api_url, **self.api_headers)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, 405)
        self.assertDictEqual(result, {"detail": 'Method "POST" not allowed.'})

    @freeze_time("2023-01-02")
    def assert_projects_sorted_descending_by_recent_article_date(
        self, device_follows_projects: bool
    ):
        # Create projects with articles at different times
        project_1, _ = self.create_project_and_article(10, "2023-01-01T12:00:00+00:00")
        self.add_article_to_project(project_1, 12, "2023-01-01T12:20:00+00:00")
        project_2, _ = self.create_project_and_article(20, "2023-01-01T12:35:00+00:00")
        self.add_article_to_project(project_2, 22, "2023-01-01T12:45:00+00:00")

        # Create projects with warnings at different times
        project_3, _ = self.create_project_and_warning(30, "2023-01-01T12:15:00+00:00")
        self.add_warning_to_project(project_3, "2023-01-01T12:16:00+00:00")
        project_4, _ = self.create_project_and_warning(40, "2023-01-01T12:36:00+00:00")
        self.add_warning_to_project(project_4, "2023-01-01T12:30:00+00:00")

        # Create device and follow all projects
        device = Device.objects.create(**mock_data.devices[0])
        if device_follows_projects:
            device.followed_projects.set([project_1, project_2, project_3, project_4])

        # Perform request
        self.api_headers[get_header_name(settings.HEADER_DEVICE_ID)] = device.device_id
        response = self.client.get(self.api_url, {"page_size": 4}, **self.api_headers)

        # Expected projects to be ordered descending by publication date
        expected_foreign_id_order = [
            project_2.pk,
            project_4.pk,
            project_1.pk,
            project_3.pk,
        ]
        response_foreign_id_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(response_foreign_id_order, expected_foreign_id_order)

    def test_followed_projects_sorted_descending_by_recent_article_date(self):
        self.assert_projects_sorted_descending_by_recent_article_date(
            device_follows_projects=True
        )

    def test_not_followed_projects_sorted_descending_by_recent_article_date(self):
        self.assert_projects_sorted_descending_by_recent_article_date(
            device_follows_projects=False
        )

    @freeze_time("2023-01-02")
    def assert_project_without_articles_sorted_below_project_with_articles(
        self, device_follows_projects: bool
    ):
        # Create project with articles
        project_1, _ = self.create_project_and_article(10, "2023-01-01T12:00:00+00:00")
        self.add_article_to_project(project_1, 12, "2023-01-01T12:20:00+00:00")

        # Create project without articles
        project_data = mock_data.projects[0]
        project_data["foreign_id"] = 20
        project_2 = Project.objects.create(**project_data)

        # Create device and follow all projects (if requested)
        device = Device.objects.create(**mock_data.devices[0])
        if device_follows_projects:
            device.followed_projects.set([project_1, project_2])

        # Perform request
        self.api_headers[get_header_name(settings.HEADER_DEVICE_ID)] = device.device_id
        response = self.client.get(self.api_url, {"page_size": 4}, **self.api_headers)

        # Expected project without articles on the bottom
        expected_foreign_id_order = [
            project_1.pk,
            project_2.pk,
        ]
        response_foreign_id_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(response_foreign_id_order, expected_foreign_id_order)

    def test_sort_followed_project_without_articles_below_project_with_articles(self):
        """
        Given a list of followed projects:
        When articles are sorted by recent article date,
        and there is a project without articles,
        it should appear on the bottom of the list
        """
        self.assert_project_without_articles_sorted_below_project_with_articles(
            device_follows_projects=True
        )

    def test_sort_not_followed_project_without_articles_below_project_with_articles(
        self,
    ):
        """
        Given a list of not followed projects:
        When articles are sorted by recent article date,
        and there is a project without articles,
        it should appear on the bottom of the list
        """
        self.assert_project_without_articles_sorted_below_project_with_articles(
            device_follows_projects=False
        )

    def test_other_projects_sorted_by_distance_with_lat_lon(self):
        """Test other projects sorted by distance with lat lon"""
        # Setup location
        # - Base location is Amsterdam Central Station
        adam_central_station = (52.379158791458494, 4.899904339167326)
        # - The closest location to the base location
        royal_palace_adam = (52.3731077480929, 4.891371824969558)
        # - The second closest location to the base location
        rijks_museam_adam = (52.36002292836369, 4.8852016757845345)
        # - The furthest location to the base location
        van_gogh_museum_adam = (52.358155575937595, 4.8811891932042055)

        project_1, _ = self.create_project_and_article(10, "2023-01-01T12:00:00+00:00")
        project_1.coordinates = {
            "lat": van_gogh_museum_adam[0],
            "lon": van_gogh_museum_adam[1],
        }
        project_1.save()

        project_2, _ = self.create_project_and_article(20, "2023-01-01T12:15:00+00:00")
        project_2.coordinates = {
            "lat": royal_palace_adam[0],
            "lon": royal_palace_adam[1],
        }
        project_2.save()

        project_3, _ = self.create_project_and_article(30, "2023-01-01T12:30:00+00:00")
        project_3.coordinates = {
            "lat": rijks_museam_adam[0],
            "lon": rijks_museam_adam[1],
        }
        project_3.save()

        # Create device, but don't follow any projects
        device = Device.objects.create(**mock_data.devices[0])

        # Perform request
        self.api_headers[get_header_name(settings.HEADER_DEVICE_ID)] = device.device_id
        response = self.client.get(
            self.api_url,
            {
                "lat": adam_central_station[0],
                "lon": adam_central_station[1],
                "page_size": 3,
            },
            **self.api_headers,
        )

        # Expected projects to be ordered from closest to furthest from the base location
        expected_foreign_id_order = [project_2.pk, project_3.pk, project_1.pk]
        response_foreign_id_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(response_foreign_id_order, expected_foreign_id_order)

    def test_pagination(self):
        """Test pagination"""
        # Create a total of 10 projects
        for i in range(1, 10 + 1):
            project_data = mock_data.projects[0]
            project_data["foreign_id"] = i * 10
            Project.objects.create(**project_data)
        self.assertEqual(len(Project.objects.all()), 10)

        device = Device.objects.create(**mock_data.devices[0])
        self.api_headers[get_header_name(settings.HEADER_DEVICE_ID)] = device.device_id

        # With page size of 4, 4 projects should be returned
        response = self.client.get(self.api_url, {"page_size": 4}, **self.api_headers)
        self.assertEqual(response.json()["page"]["number"], 1)
        self.assertEqual(response.json()["page"]["size"], 4)
        self.assertEqual(response.json()["page"]["totalElements"], 10)
        self.assertEqual(response.json()["page"]["totalPages"], 3)
        self.assertEqual(len(response.json()["result"]), 4)

        # The next URL should be available with the same pagination settings
        next_url = response.json()["_links"]["next"]["href"]

        # With page size of 4, the next 4 projects should be returned
        response = self.client.get(next_url, **self.api_headers)
        self.assertEqual(response.json()["page"]["number"], 2)
        self.assertEqual(response.json()["page"]["size"], 4)
        self.assertEqual(response.json()["page"]["totalElements"], 10)
        self.assertEqual(response.json()["page"]["totalPages"], 3)
        self.assertEqual(len(response.json()["result"]), 4)

        next_url = response.json()["_links"]["next"]["href"]

        # With page size of 4, the last 2 projects should be returned
        response = self.client.get(next_url, **self.api_headers)
        self.assertEqual(response.json()["page"]["number"], 3)
        self.assertEqual(response.json()["page"]["size"], 4)
        self.assertEqual(response.json()["page"]["totalElements"], 10)
        self.assertEqual(response.json()["page"]["totalPages"], 3)
        self.assertEqual(len(response.json()["result"]), 2)

    def test_get_only_active_projects(self):
        """Check if only active projects are returned"""
        my_device = Device.objects.create(
            device_id="foobar", firebase_token="foobar", os="foobar"
        )
        self.api_headers[
            get_header_name(settings.HEADER_DEVICE_ID)
        ] = my_device.device_id

        unfollowed_project_data = mock_data.projects[0]
        unfollowed_project_data["title"] = "this_unfollowed_project_will_be_deactivated"
        unfollowed_project_data["foreign_id"] = 888

        # First create new project that is active and not followed
        unfollowed_project = Project.objects.create(**unfollowed_project_data)
        unfollowed_project.active = True
        unfollowed_project.save()

        followed_project_data = mock_data.projects[0]
        followed_project_data["title"] = "this_followed_project_will_be_deactivated"
        followed_project_data["foreign_id"] = 999

        followed_project = Project.objects.create(**followed_project_data)
        followed_project.active = True
        followed_project.save()

        my_device.followed_projects.add(followed_project)
        my_device.save()

        # These active projects should be returned
        response = self.client.get(
            self.api_url, {"page_size": 9999}, **self.api_headers
        )
        res_titles = [x.get("title") for x in response.data["result"]]
        self.assertIn(unfollowed_project.title, res_titles)
        self.assertIn(followed_project.title, res_titles)

        # Then deactivate both projects
        unfollowed_project.deactivate()
        followed_project.deactivate()

        # The projects should not be returned now
        response = self.client.get(
            self.api_url, {"page_size": 9999}, **self.api_headers
        )
        res_titles = [x.get("title") for x in response.data["result"]]
        self.assertNotIn(unfollowed_project.title, res_titles)
        self.assertNotIn(followed_project.title, res_titles)
