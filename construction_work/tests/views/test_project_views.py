import pathlib
from datetime import datetime
from os.path import join

from django.conf import settings
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker

from construction_work.models.article_models import (
    Article,
    ArticleImage,
    ArticleImageSource,
)
from construction_work.models.manage_models import (
    Device,
    Image,
    ProjectManager,
    WarningImage,
    WarningMessage,
)
from construction_work.models.project_models import Project
from construction_work.tests import mock_data
from construction_work.utils.date_utils import translate_timezone as tt
from construction_work.utils.patch_utils import create_image_file
from core.tests.test_authentication import BasicAPITestCase

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]


@override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
class BaseTestProjectView(BasicAPITestCase):
    """Abstract base class for API tests"""

    def setUp(self):
        super().setUp()

        self.maxDiff = None

        # Create needed database extensions
        connection = connections[DEFAULT_DB_ALIAS]
        cursor = connection.cursor()
        cursor.execute("CREATE EXTENSION pg_trgm")
        cursor.execute("CREATE EXTENSION unaccent")

    def tearDown(self) -> None:
        super().tearDown()

        Project.objects.all().delete()
        Article.objects.all().delete()
        WarningMessage.objects.all().delete()

    def create_project_and_article(self, project_foreign_id, article_pub_date, project_pub_date=None):
        """Create project and article"""
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = project_foreign_id
        if project_pub_date:
            project_data["publication_date"] = project_pub_date
        project = Project.objects.create(**project_data)

        article_data = mock_data.articles[0].copy()
        article_data["foreign_id"] = project_foreign_id + 1
        article_data["publication_date"] = article_pub_date
        article = Article.objects.create(**article_data)
        article.projects.add(project)

        return project, article

    def create_project_and_warning(self, project_foreign_id, pub_date):
        """Create project and warning"""
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = project_foreign_id
        project = Project.objects.create(**project_data)

        warning_data = mock_data.warning_message.copy()
        warning_data["project"] = project
        warning = WarningMessage.objects.create(**warning_data)
        warning.publication_date = pub_date
        warning.save()

        return project, warning

    def add_article_to_project(self, project: Project, foreign_id, pub_date):
        """Add article to projects"""
        article_data = mock_data.articles[0].copy()
        article_data["foreign_id"] = foreign_id
        article_data["publication_date"] = pub_date
        article = Article.objects.create(**article_data)
        article.projects.add(project)
        return article

    def add_warning_to_project(self, project: Project, pub_date):
        """Add warning to project"""
        warning_data = mock_data.warning_message.copy()
        warning_data["project"] = project
        warning = WarningMessage.objects.create(**warning_data)
        warning.publication_date = pub_date
        warning.save()

        return warning


class TestProjectListView(BaseTestProjectView):
    """Tests for getting all projects via API"""

    def setUp(self):
        super().setUp()
        self.api_url = reverse("construction-work:project-list")

        # Base location (Amsterdam Central Station)
        self.base_location = (52.379158791458494, 4.899904339167326)
        # Test locations from closest to furthest from base
        self.test_locations = [
            (52.3731077480929, 4.891371824969558),    # Royal Palace (closest)
            (52.36002292836369, 4.8852016757845345),   # Rijksmuseum (middle)
            (52.358155575937595, 4.8811891932042055),  # Van Gogh Museum (furthest)
        ]

    def tearDown(self) -> None:
        Project.objects.all().delete()
        Article.objects.all().delete()
        Device.objects.all().delete()
        super().tearDown()

    def create_project_with_location(self, foreign_id: int, location_index: int) -> Project:
        """Helper to create project with specific location"""
        location = self.test_locations[location_index]
        return Project.objects.create(**{
            **mock_data.projects[0].copy(),
            "foreign_id": foreign_id,
            "coordinates_lat": location[0],
            "coordinates_lon": location[1]
        })

    def create_projects_with_articles(self, base_foreign_id: int, article_pub_dates: list[str], project_pub_dates: list[str] = None) -> list[Project]:
        """Helper to create multiple projects with articles at given timestamps"""
        projects = []
        for i, article_timestamp in enumerate(article_pub_dates):
            project, _ = self.create_project_and_article(
                base_foreign_id + i, 
                article_timestamp,
                project_pub_dates[i] if project_pub_dates else None
            )
            projects.append(project)
        return projects

    @freeze_time("2023-01-02")
    def test_followed_projects_with_articles_and_device_location(self):
        """
        Test followed projects with articles when device location is provided:
        - Projects with articles should be sorted by most recent article first
        - Projects without articles should be sorted by distance
        """
        # Create projects with articles
        article_projects = self.create_projects_with_articles(10, [
            "2023-01-01T12:00:00+00:00",  # Oldest
            "2023-01-01T12:30:00+00:00",  # Newest
            "2023-01-01T12:15:00+00:00",  # Middle
        ])

        # Create projects with only locations
        location_projects = [
            self.create_project_with_location(20, 1),  # Middle
            self.create_project_with_location(30, 0),  # Closest
            self.create_project_with_location(40, 2),  # Furthest
        ]

        # Create device and follow all projects
        device = Device.objects.create(**mock_data.devices[0].copy())
        device.followed_projects.set(article_projects + location_projects)

        # Perform request with location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {
                "lat": self.base_location[0],
                "lon": self.base_location[1],
                "page_size": 10
            },
            headers=self.api_headers
        )

        # Expected: newest article first, then oldest article, then by distance
        expected_order = [
            article_projects[1].pk,  # Newest article
            article_projects[2].pk,  # Middle article
            article_projects[0].pk,  # Oldest article
            location_projects[1].pk, # Closest location
            location_projects[0].pk, # Middle location
            location_projects[2].pk, # Furthest location
        ]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)

    @freeze_time("2023-01-02")
    def test_followed_projects_with_articles_no_device_location(self):
        """
        Test followed projects with articles when no device location is provided:
        - Projects with articles should be sorted by most recent article first
        - Then by project publication date for those without articles
        """
        # Create projects with articles at different times
        article_projects = self.create_projects_with_articles(10, [
            "2023-01-01T12:15:00+00:00",  # Middle
            "2023-01-01T12:00:00+00:00",  # Oldest
            "2023-01-01T12:30:00+00:00",  # Newest
        ])

        # Create projects without articles but with different publication dates
        no_article_projects = []
        project_data = mock_data.projects[0].copy()
        
        # Earlier publication date
        project_data["foreign_id"] = 30
        project_data["publication_date"] = "2023-01-01T11:00:00+00:00"
        no_article_projects.append(Project.objects.create(**project_data))
        
        # Later publication date
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 40
        project_data["publication_date"] = "2023-01-01T11:30:00+00:00"
        no_article_projects.append(Project.objects.create(**project_data))

        # Create device and follow all projects
        device = Device.objects.create(**mock_data.devices[0].copy())
        device.followed_projects.set(article_projects + no_article_projects)

        # Perform request without location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {"page_size": 10},
            headers=self.api_headers
        )

        expected_order = [
            article_projects[2].pk,    # Newest article
            article_projects[0].pk,    # Middle article
            article_projects[1].pk,    # Oldest article
            no_article_projects[1].pk, # Later publication date
            no_article_projects[0].pk, # Earlier publication date
        ]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)

    @freeze_time("2023-01-02")
    def test_unfollowed_projects_with_device_location(self):
        """
        Test unfollowed projects when device location is provided:
        - Projects should be sorted by distance only
        """
        # Create projects at different locations
        projects = [
            self.create_project_with_location(10, 1),  # Middle
            self.create_project_with_location(20, 2),  # Furthest
            self.create_project_with_location(30, 0),  # Closest
        ]

        # Create device but don't follow any projects
        device = Device.objects.create(**mock_data.devices[0].copy())

        # Perform request with location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {
                "lat": self.base_location[0],
                "lon": self.base_location[1],
                "page_size": 3
            },
            headers=self.api_headers
        )

        expected_order = [projects[2].pk, projects[0].pk, projects[1].pk]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)

    @freeze_time("2023-01-02")
    def test_unfollowed_projects_without_device_location(self):
        """
        Test unfollowed projects when no device location is provided:
        - Projects should be sorted by most recent project publication date
        """
        # Create projects with different publication dates
        projects = []
        project_data = mock_data.projects[0].copy()
        
        # Oldest
        project_data["foreign_id"] = 10
        project_data["publication_date"] = "2023-01-01T12:00:00+00:00"
        projects.append(Project.objects.create(**project_data))
        
        # Newest
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 20
        project_data["publication_date"] = "2023-01-01T12:30:00+00:00"
        projects.append(Project.objects.create(**project_data))
        
        # Middle
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 30
        project_data["publication_date"] = "2023-01-01T12:15:00+00:00"
        projects.append(Project.objects.create(**project_data))

        # Create device but don't follow any projects
        device = Device.objects.create(**mock_data.devices[0].copy())

        # Perform request without location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {"page_size": 3},
            headers=self.api_headers
        )

        expected_order = [
            projects[1].pk,  # Newest publication date
            projects[2].pk,  # Middle publication date
            projects[0].pk,  # Oldest publication date
        ]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)

    @freeze_time("2023-01-02")
    def test_unfollowed_projects_with_articles_no_device_location(self):
        """
        Test unfollowed projects with articles when no device location is provided.
        Projects should be sorted by project publication date only,
        ignoring article dates completely.
        """

        # Create unfollowed projects with articles
        unfollowed_projects = self.create_projects_with_articles(
            base_foreign_id=20,
            article_pub_dates=[
                "2023-01-01T12:30:00+00:00",
                "2023-01-01T12:15:00+00:00",
                "2023-01-01T12:00:00+00:00",
            ],
            project_pub_dates=[
                "2023-01-01T12:00:00+00:00", # Oldest
                "2023-01-01T12:15:00+00:00", # Middle
                "2023-01-01T12:30:00+00:00", # Newest
            ]
        )

        # Create device but don't follow any projects
        device = Device.objects.create(**mock_data.devices[0].copy())

        # Perform request without location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {"page_size": 10},
            headers=self.api_headers
        )

        # Should be ordered by project publication date only,
        # completely ignoring article dates
        expected_order = [
            unfollowed_projects[2].pk,  # Newest project publication date (12:30)
            unfollowed_projects[1].pk,  # Middle project publication date (12:15)
            unfollowed_projects[0].pk,  # Oldest project publication date (12:00)
        ]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)

    @freeze_time("2023-01-02")
    def test_mixed_followed_and_unfollowed_with_device_location(self):
        """
        Test mixed followed and unfollowed projects with location:
        - Followed projects with articles should be first, sorted by article date
        - Followed projects without articles should be next, sorted by distance
        - Unfollowed projects should be last, sorted by distance
        """
        # Create followed projects with articles
        followed_article_projects = self.create_projects_with_articles(10, [
            "2023-01-01T12:00:00+00:00",  # Older
            "2023-01-01T12:30:00+00:00",  # Newer
        ])

        # Create followed projects with only locations
        followed_location_projects = [
            self.create_project_with_location(30, 0),  # Closest
            self.create_project_with_location(40, 2),  # Furthest
        ]

        # Create unfollowed projects with locations
        unfollowed_projects = [
            self.create_project_with_location(50, 1),  # Middle distance
            self.create_project_with_location(60, 2),  # Furthest
        ]

        # Create device and follow specific projects
        device = Device.objects.create(**mock_data.devices[0].copy())
        device.followed_projects.set(followed_article_projects + followed_location_projects)

        # Perform request with location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {
                "lat": self.base_location[0],
                "lon": self.base_location[1],
                "page_size": 6
            },
            headers=self.api_headers
        )

        expected_order = [
            followed_article_projects[1].pk,  # Followed, newest article
            followed_article_projects[0].pk,  # Followed, older article
            followed_location_projects[0].pk, # Followed, closest
            followed_location_projects[1].pk, # Followed, furthest
            unfollowed_projects[0].pk,       # Unfollowed, middle distance
            unfollowed_projects[1].pk,       # Unfollowed, furthest
        ]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)

    @freeze_time("2023-01-02")
    def test_mixed_followed_and_unfollowed_without_device_location(self):
        """
        Test mixed followed and unfollowed projects without device location:
        - Followed projects with articles should be first, sorted by article date
        - Followed projects without articles should be next, sorted by project publication date
        - Unfollowed projects should be last, sorted by project publication date
        """
        # Create followed projects with articles
        followed_article_projects = self.create_projects_with_articles(
            base_foreign_id=10,
            article_pub_dates=[
                "2023-01-01T12:00:00+00:00",  # Older
                "2023-01-01T12:30:00+00:00",  # Newer
            ]
        )

        # Create followed projects without articles but with different publication dates
        followed_no_article_projects = []
        project_data = mock_data.projects[0].copy()
        
        # Earlier publication date
        project_data["foreign_id"] = 30
        project_data["publication_date"] = "2023-01-01T11:00:00+00:00"
        followed_no_article_projects.append(Project.objects.create(**project_data))
        
        # Later publication date
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 40
        project_data["publication_date"] = "2023-01-01T11:30:00+00:00"
        followed_no_article_projects.append(Project.objects.create(**project_data))

        # Create unfollowed projects with articles
        unfollowed_projects = self.create_projects_with_articles(
            base_foreign_id=50,
            article_pub_dates=[
                "2023-01-01T12:00:00+00:00",
                "2023-01-01T12:00:00+00:00",
                "2023-01-01T12:00:00+00:00",
            ],
            project_pub_dates=[
                "2023-01-01T12:00:00+00:00", # Oldest
                "2023-01-01T12:15:00+00:00", # Middle
                "2023-01-01T12:30:00+00:00", # Newest
            ]
        )

        # Create device and follow specific projects
        device = Device.objects.create(**mock_data.devices[0].copy())
        device.followed_projects.set(followed_article_projects + followed_no_article_projects)

        # Perform request without location
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id
        response = self.client.get(
            self.api_url,
            {"page_size": 10},
            headers=self.api_headers
        )

        expected_order = [
            followed_article_projects[1].pk,    # Followed, newest article
            followed_article_projects[0].pk,    # Followed, older article
            followed_no_article_projects[1].pk, # Followed, later publication date
            followed_no_article_projects[0].pk, # Followed, earlier publication date
            unfollowed_projects[2].pk,          # Unfollowed, newest
            unfollowed_projects[1].pk,          # Unfollowed, middle
            unfollowed_projects[0].pk,          # Unfollowed, oldest
        ]
        actual_order = [x["id"] for x in response.json()["result"]]
        self.assertEqual(actual_order, expected_order)


    def test_pagination(self):
        """Test pagination"""
        # Create a total of 10 projects
        for i in range(1, 10 + 1):
            project_data = mock_data.projects[0].copy()
            project_data["foreign_id"] = i * 10
            Project.objects.create(**project_data)
        self.assertEqual(len(Project.objects.all()), 10)

        device = Device.objects.create(**mock_data.devices[0].copy())
        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id

        # With page size of 4, 4 projects should be returned
        response = self.client.get(
            self.api_url, {"page_size": 4}, headers=self.api_headers
        )
        self.assertEqual(response.json()["page"]["number"], 1)
        self.assertEqual(response.json()["page"]["size"], 4)
        self.assertEqual(response.json()["page"]["totalElements"], 10)
        self.assertEqual(response.json()["page"]["totalPages"], 3)
        self.assertEqual(len(response.json()["result"]), 4)

        # The next URL should be available with the same pagination settings
        next_url = response.json()["_links"]["next"]["href"]

        # With page size of 4, the next 4 projects should be returned
        response = self.client.get(next_url, headers=self.api_headers)
        self.assertEqual(response.json()["page"]["number"], 2)
        self.assertEqual(response.json()["page"]["size"], 4)
        self.assertEqual(response.json()["page"]["totalElements"], 10)
        self.assertEqual(response.json()["page"]["totalPages"], 3)
        self.assertEqual(len(response.json()["result"]), 4)

        next_url = response.json()["_links"]["next"]["href"]

        # With page size of 4, the last 2 projects should be returned
        response = self.client.get(next_url, headers=self.api_headers)
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
        self.api_headers[settings.HEADER_DEVICE_ID] = my_device.device_id

        unfollowed_project_data = mock_data.projects[0].copy()
        unfollowed_project_data["title"] = "this_unfollowed_project_will_be_deactivated"
        unfollowed_project_data["foreign_id"] = 888

        # First create new project that is active and not followed
        unfollowed_project = Project.objects.create(**unfollowed_project_data)
        unfollowed_project.active = True
        unfollowed_project.save()

        followed_project_data = mock_data.projects[0].copy()
        followed_project_data["title"] = "this_followed_project_will_be_deactivated"
        followed_project_data["foreign_id"] = 999

        followed_project = Project.objects.create(**followed_project_data)
        followed_project.active = True
        followed_project.save()

        my_device.followed_projects.add(followed_project)
        my_device.save()

        # These active projects should be returned
        response = self.client.get(
            self.api_url, {"page_size": 9999}, headers=self.api_headers
        )
        res_titles = [x.get("title") for x in response.data["result"]]
        self.assertIn(unfollowed_project.title, res_titles)
        self.assertIn(followed_project.title, res_titles)

        # Then deactivate both projects
        unfollowed_project.deactivate()
        followed_project.deactivate()

        # The projects should not be returned now
        response = self.client.get(
            self.api_url, {"page_size": 9999}, headers=self.api_headers
        )
        res_titles = [x.get("title") for x in response.data["result"]]
        self.assertNotIn(unfollowed_project.title, res_titles)
        self.assertNotIn(followed_project.title, res_titles)


class TestProjectDetailsView(BaseTestProjectView):
    def setUp(self):
        super().setUp()

        self.api_url = reverse("construction-work:get-project")

    def test_missing_device_id(self):
        """Test call without device id"""
        response = self.client.get(self.api_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_missing_project_id(self):
        """Test call without project id"""
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        params = {
            "lat": 52.379158791458494,
            "lon": 4.899904339167326,
            "article_max_age": 10,
        }
        response = self.client.get(self.api_url, params, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_project_does_not_exists(self):
        """Test call when project does not exist"""
        new_device_id = "new_foobar_device"
        self.api_headers[settings.HEADER_DEVICE_ID] = new_device_id
        params = {
            "id": 9999,
            "lat": 52.379158791458494,
            "lon": 4.899904339167326,
            "article_max_age": 10,
        }
        response = self.client.get(self.api_url, params, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)

    def test_get_project_details(self):
        """Test getting project details"""
        project = Project.objects.create(**mock_data.projects[0].copy())

        new_device_id = "new_foobar_device"
        self.api_headers[settings.HEADER_DEVICE_ID] = new_device_id
        params = {
            "id": project.pk,
            "lat": 52.379158791458494,
            "lon": 4.899904339167326,
            "article_max_age": 10,
        }
        response = self.client.get(self.api_url, params, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertEqual(response.json()["id"], project.pk)


class TestProjectSearchView(BaseTestProjectView):
    """Test searching text in project model"""

    def setUp(self):
        super().setUp()
        self.api_url = reverse("construction-work:project-search")

        for project in mock_data.projects:
            Project.objects.create(**project)

    def test_no_text(self):
        """Test search without a string"""
        query = {
            "query_fields": "title,subtitle",
            "fields": "title,subtitle",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_text_to_short(self):
        """Test for text lower than minimal length"""
        query = {
            "text": "x" * (settings.MIN_SEARCH_QUERY_LENGTH - 1),
            "query_fields": "title,subtitle",
            "fields": "title,subtitle",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_search_in_field_not_part_of_model(self):
        """Test search in field that is not part of the project model"""
        query = {
            "text": "title",
            "query_fields": "foobar",
            "fields": "title,subtitle",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_invalid_model_return_field(self):
        """Test request return fields that are not part of the model"""
        query = {
            "text": "title",
            "query_fields": "title,subtitle",
            "fields": "foobar",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def assert_projects_found(self, search_term, projects_found=1):
        query = {
            "text": search_term,
            "query_fields": "title,subtitle",
            "fields": "title,subtitle",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["result"]), projects_found)

    def test_search_project(self):
        self.assert_projects_found("title first project")
        # search for full words
        self.assert_projects_found("title")
        self.assert_projects_found("first")
        self.assert_projects_found("project")
        # search for part of words
        self.assert_projects_found("tit")
        self.assert_projects_found("tit fir")
        self.assert_projects_found("tit fir pro")
        self.assert_projects_found("pro tit fir")
        self.assert_projects_found("tle")
        self.assert_projects_found("tle ject")
        # search with small typos
        self.assert_projects_found("titel")
        self.assert_projects_found("pjorect")
        self.assert_projects_found("fisrt pjorect")

    def test_use_nonsense_search_term(self):
        self.assert_projects_found("foobar", 0)

    def test_title_query_field_is_given_priority(self):
        """Test that matches in title field are prioritized over other fields"""
        Project.objects.all().delete()
        # Create projects with search term in different fields
        project1 = Project.objects.create(
            foreign_id=1,
            title="something else",
            subtitle="search_term is in the beginning of this subtitle",
        )
        project2 = Project.objects.create(
            foreign_id=2,
            title="this sentence will and with an embedded_search_term",
            subtitle="something else",
        )

        # Search across both title and subtitle fields
        query = {
            "text": "search_term",
            "query_fields": "title,subtitle",
            "fields": "id,title,subtitle",
            "page_size": 10,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        results = response.json()["result"]

        # Project with match in title should appear first
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], project2.pk)
        self.assertEqual(results[1]["id"], project1.pk)

    def test_search_project_and_follow_links(self):
        """Test search for projects"""
        search_text = "title"
        query = {
            "text": search_text,
            "query_fields": "title,subtitle",
            "fields": "title,subtitle",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["result"]), 1)

        project_data = response.json()["result"][0]
        self.assertTrue(search_text in project_data["title"])

        next_page = response.json()["_links"]["next"]["href"]

        # Go to next page, and check results
        response = self.client.get(next_page, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["result"]), 1)

        project_data = response.json()["result"][0]
        self.assertTrue(search_text in project_data["title"])

    def test_get_only_active_projects(self):
        """Check if only active projects are returned"""
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"

        project_data = mock_data.projects[0].copy()
        project_data["title"] = "this_project_will_be_deactivated"
        project_data["foreign_id"] = 999

        # First create new project that is active
        new_project = Project.objects.create(**project_data)
        new_project.active = True
        new_project.save()

        # This active project should be returned
        query = {
            "text": new_project.title,
            "query_fields": "title",
            "fields": "title",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)
        res_titles = [x.get("title") for x in response.data["result"]]
        self.assertIn(new_project.title, res_titles)

        # Then deactivate this project
        new_project.deactivate()

        # The project should not be returned now
        response = self.client.get(self.api_url, query, headers=self.api_headers)
        res_titles = [x.get("title") for x in response.data["result"]]
        self.assertNotIn(new_project.title, res_titles)

    def test_search_text_query_fields(self):
        """Test search for projects"""
        search_text = "title"
        query = {
            "text": search_text,
            "query_fields": "id,title,subtitle",
            "fields": "title,subtitle",
            "page_size": 1,
            "page": 1,
        }
        response = self.client.get(self.api_url, query, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        result = response.json()["result"]
        self.assertEqual(len(result), 1)


class TestFollowProjectView(BaseTestProjectView):
    def setUp(self):
        super().setUp()

        self.api_url = reverse("construction-work:follow-project")

        for project in mock_data.projects:
            Project.objects.create(**project)

    def test_missing_device_id(self):
        """Test missing device id"""
        project = Project.objects.first()
        foreign_id = project.foreign_id

        data = {"foreign_id": foreign_id}
        response = self.client.post(self.api_url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_missing_foreign_id(self):
        """Test missing foreign id"""
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        data = {}
        response = self.client.post(self.api_url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_project_does_not_exist(self):
        """Test call but project does not exist"""
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        data = {"id": 9999}
        response = self.client.post(self.api_url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)

    def test_existing_device_follows_existing_project(self):
        """Test new device follows existing project"""
        project = Project.objects.first()
        project_id = project.pk

        # Setup device and follow project
        device_id = "foobar"
        device = Device(device_id=device_id)
        device.save()

        # Perform API call and check status
        self.api_headers[settings.HEADER_DEVICE_ID] = device_id
        data = {"id": project_id}
        response = self.client.post(self.api_url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        # Device should now exist with followed project
        device: Device = Device.objects.filter(device_id=device_id).first()
        self.assertIsNotNone(device)
        self.assertIn(project, device.followed_projects.all())

    def test_new_device_follows_existing_project(self):
        """Test new device follows existing project"""
        project = Project.objects.first()
        project_id = project.pk

        # Test if device did not yet exist
        new_device_id = "foobar"
        device: Device = Device.objects.filter(device_id=new_device_id).first()
        self.assertIsNone(device)

        # Perform API call and check status
        self.api_headers[settings.HEADER_DEVICE_ID] = new_device_id
        data = {"id": project_id}
        response = self.client.post(self.api_url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        # Device should now exist with followed project
        device: Device = Device.objects.filter(device_id=new_device_id).first()
        self.assertIsNotNone(device)
        self.assertIn(project, device.followed_projects.all())

    def test_existing_device_unfollows_existing_project(self):
        """Test unfollow existing project with existing device"""
        # Setup device and follow project
        device_id = "foobar"
        project = Project.objects.first()
        project_id = project.pk
        device = Device(device_id=device_id)
        device.save()
        device.followed_projects.add(project)

        # Perform API call and check status
        self.api_headers[settings.HEADER_DEVICE_ID] = device_id
        data = {"id": project_id}
        response = self.client.delete(self.api_url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        # Project should not be part of device followed projects
        self.assertNotIn(project, device.followed_projects.all())

    def test_unfollow_not_existing_project(self):
        """Test unfollowing not existing project"""
        # Setup device and follow project
        device_id = "foobar"
        device = Device(device_id=device_id)
        device.save()

        # Perform API call and check status
        self.api_headers[settings.HEADER_DEVICE_ID] = device_id
        data = {"id": 9999}
        response = self.client.delete(self.api_url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)

    def test_unfollow_project_that_device_is_not_following(self):
        """Test unfollow existing project with existing device"""
        # Setup device and follow project
        project = Project.objects.first()
        project_id = project.pk

        device_id = "foobar"
        device = Device(device_id=device_id)
        device.save()

        # Perform API call and check status
        self.api_headers[settings.HEADER_DEVICE_ID] = device_id
        data = {"id": project_id}
        response = self.client.delete(self.api_url, data=data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

        # Device should have no followed projects
        self.assertEqual(0, len(device.followed_projects.all()))


class TestFollowedProjectsArticlesView(BaseTestProjectView):
    def setUp(self):
        super().setUp()

        self.api_url = reverse("construction-work:followed-projects-with-articles")

    def test_missing_device_id(self):
        """Test missing device id"""
        self.api_headers[settings.HEADER_DEVICE_ID] = None
        response = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_device_does_not_exist(self):
        """Test device does not exist"""
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        response = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_device_follows_hidden_project(self):
        project_data = mock_data.projects[0].copy()
        project_data["hidden"] = True
        hidden_project = Project.objects.create(**project_data)

        article_data = mock_data.articles[0].copy()
        article = Article.objects.create(**article_data)
        article.projects.add(hidden_project)

        device = Device.objects.create(**mock_data.devices[0].copy())
        device.followed_projects.add(hidden_project)

        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id

        response = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @freeze_time("2023-01-10")
    def test_get_recent_articles(self):
        """Test get recent articles"""
        # Project with TWO recent articles
        project_1, article_1 = self.create_project_and_article(
            10, "2023-01-08T12:00:00+00:00"
        )
        warning_1 = self.add_warning_to_project(project_1, "2023-01-08T12:00:00+00:00")
        article_2 = self.add_article_to_project(
            project_1, 12, "2023-01-08T12:00:00+00:00"
        )

        # Project with ONE recent article
        project_2, article_3 = self.create_project_and_article(
            20, "2023-01-05T12:00:00+00:00"
        )
        article_4 = self.add_article_to_project(
            project_2, 22, "2023-01-07T12:00:00+00:00"
        )

        # Project with NO recent articles
        project_3, article_5 = self.create_project_and_article(
            30, "2023-01-01T12:00:00+00:00"
        )
        article_6 = self.add_article_to_project(
            project_3, 32, "2023-01-01T12:00:00+00:00"
        )

        # Create device and follow all projects
        device = Device.objects.create(**mock_data.devices[0].copy())
        device.followed_projects.set([project_1, project_2, project_3])

        self.api_headers[settings.HEADER_DEVICE_ID] = device.device_id

        def assert_total_returned_articles(max_age=0):
            params = {"article_max_age": max_age}
            _response = self.client.get(
                self.api_url, params, headers=self.api_headers
            ).json()

            _total_returned_articles = 0
            for key in _response:
                article_count = len(_response[key])
                _total_returned_articles += article_count

            return _total_returned_articles, _response

        total_returned_articles, response = assert_total_returned_articles(max_age=3)
        self.assertEqual(total_returned_articles, 4)

        target_tzinfo = datetime.fromisoformat(
            response[str(project_1.pk)][0]["modification_date"]
        ).tzinfo

        expected_result = {
            str(project_1.pk): [
                {
                    "meta_id": {
                        "id": article_1.pk,
                        "type": "article",
                    },
                    "modification_date": tt(
                        str(article_1.modification_date), target_tzinfo
                    ),
                },
                {
                    "meta_id": {
                        "id": article_2.pk,
                        "type": "article",
                    },
                    "modification_date": tt(
                        str(article_2.modification_date), target_tzinfo
                    ),
                },
                {
                    "meta_id": {
                        "id": warning_1.pk,
                        "type": "warning",
                    },
                    "modification_date": tt(
                        str(warning_1.modification_date), target_tzinfo
                    ),
                },
            ],
            str(project_2.pk): [
                {
                    "meta_id": {"id": article_4.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_4.modification_date), target_tzinfo
                    ),
                }
            ],
            str(project_3.pk): [],
        }
        self.assertDictEqual(response, expected_result)

        total_returned_articles, response = assert_total_returned_articles(max_age=10)
        self.assertEqual(total_returned_articles, 7)
        expected_result = {
            str(project_1.pk): [
                {
                    "meta_id": {"id": article_1.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_1.modification_date), target_tzinfo
                    ),
                },
                {
                    "meta_id": {"id": article_2.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_2.modification_date), target_tzinfo
                    ),
                },
                {
                    "meta_id": {"id": warning_1.pk, "type": "warning"},
                    "modification_date": tt(
                        str(warning_1.modification_date), target_tzinfo
                    ),
                },
            ],
            str(project_2.pk): [
                {
                    "meta_id": {"id": article_3.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_3.modification_date), target_tzinfo
                    ),
                },
                {
                    "meta_id": {"id": article_4.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_4.modification_date), target_tzinfo
                    ),
                },
            ],
            str(project_3.pk): [
                {
                    "meta_id": {"id": article_5.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_5.modification_date), target_tzinfo
                    ),
                },
                {
                    "meta_id": {"id": article_6.pk, "type": "article"},
                    "modification_date": tt(
                        str(article_6.modification_date), target_tzinfo
                    ),
                },
            ],
        }
        self.assertDictEqual(response, expected_result)


class TestWarningMessageDetailView(BaseTestProjectView):
    def setUp(self) -> None:
        super().setUp()
        call_command("flush", verbosity=0, interactive=False)

        self.api_url = reverse("construction-work:get-warning")

        for project in mock_data.projects:
            Project.objects.create(**project)

        for project_manager in mock_data.project_managers:
            ProjectManager.objects.create(**project_manager)

    def create_message_from_data(self, data) -> WarningMessage:
        """Create message from data"""
        project_obj = Project.objects.filter(
            foreign_id=data.get("project_foreign_id")
        ).first()
        project_obj.save()

        project_manager = ProjectManager.objects.filter(
            email=data.get("project_manager_email")
        ).first()
        project_manager.projects.add(project_obj)

        new_message = WarningMessage(
            title=data.get("title"),
            body=data.get("body"),
            project=project_obj,
            project_manager=project_manager,
        )
        new_message.save()
        return new_message

    def test_get_warning_message_success(self):
        """Test get warning message"""
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "project_foreign_id": 2048,
            "project_manager_email": "mock0@amsterdam.nl",
        }
        new_message = self.create_message_from_data(data)

        result = self.client.get(
            f"{self.api_url}?id={new_message.pk}", headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        target_dt = datetime.fromisoformat(result.data["publication_date"])

        expected_result = {
            "id": new_message.pk,
            "images": [],
            "title": "foobar title",
            "body": "foobar body",
            "project": new_message.project.pk,
            "publication_date": tt(str(new_message.publication_date), target_dt.tzinfo),
            "modification_date": tt(
                str(new_message.modification_date), target_dt.tzinfo
            ),
            "author_email": "mock0@amsterdam.nl",
            "meta_id": {"id": new_message.pk, "type": "warning"},
            "notification_sent": False,
        }
        self.assertDictEqual(result.data, expected_result)

    def test_get_warning_message_with_image(self):
        """Test get warning message with image"""
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "project_foreign_id": 2048,
            "project_manager_email": "mock0@amsterdam.nl",
        }
        new_warning_message = self.create_message_from_data(data)

        warning_image_data = {
            "warning_id": new_warning_message.pk,
        }
        warning_image = WarningImage.objects.create(**warning_image_data)

        image_data = mock_data.images[0].copy()
        image_path = join(
            ROOT_DIR, "construction_work/tests/image_data/small_image.png"
        )
        image_data["image"] = create_image_file(image_path)
        image = Image.objects.create(**image_data)
        warning_image.images.add(image)

        result = self.client.get(
            f"{self.api_url}?id={new_warning_message.pk}", headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        target_dt = datetime.fromisoformat(result.data["publication_date"])
        expected_result = {
            "id": new_warning_message.pk,
            "images": [
                {
                    "id": image.pk,
                    "sources": [
                        {
                            "uri": "http://testserver/construction-work/media/images/image.jpg",
                            "width": 10,
                            "height": 10,
                        }
                    ],
                    "landscape": False,
                    "alternativeText": "square image",
                }
            ],
            "title": "foobar title",
            "body": "foobar body",
            "project": new_warning_message.project.pk,
            "publication_date": tt(
                str(new_warning_message.publication_date), target_dt.tzinfo
            ),
            "modification_date": tt(
                str(new_warning_message.modification_date), target_dt.tzinfo
            ),
            "author_email": "mock0@amsterdam.nl",
            "meta_id": {"id": new_warning_message.pk, "type": "warning"},
            "notification_sent": False,
        }
        self.assertDictEqual(result.json(), expected_result)

    def test_get_warning_message_inactive_project(self):
        """Tet get warning message"""
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "project_foreign_id": 2048,
            "project_manager_email": "mock0@amsterdam.nl",
        }

        new_message = self.create_message_from_data(data)

        # Deactivate the project
        project_obj = Project.objects.filter(foreign_id=2048).first()
        project_obj.deactivate()

        result = self.client.get(
            f"{self.api_url}?id={new_message.pk}", headers=self.api_headers
        )
        self.assertEqual(result.status_code, 404)

    def test_get_warning_message_no_identifier(self):
        """Test get waring message without identifier"""
        result = self.client.get(f"{self.api_url}", headers=self.api_headers)
        self.assertEqual(result.status_code, 400)

    def test_get_warning_message_invalid_id(self):
        """Test get warning message with invalid identifier"""
        result = self.client.get(f"{self.api_url}?id=9999", headers=self.api_headers)
        self.assertEqual(result.status_code, 404)


class TestArticleListView(BaseTestProjectView):
    """Test multiple articles view"""

    def setUp(self):
        """Setup test db"""
        super().setUp()
        self.api_url = reverse("construction-work:article-list")

        projects = []
        for project_data in mock_data.projects:
            project = Project.objects.create(**project_data)
            projects.append(project)

        articles = []
        for article_data in mock_data.articles:
            article = Article.objects.create(**article_data)
            articles.append(article)

        articles[0].projects.add(projects[0])
        articles[0].publication_date = "2023-01-01T12:00:00+00:00"
        articles[0].save()

        articles[1].projects.add(projects[1])
        articles[1].publication_date = "2023-01-01T11:00:00+00:00"
        articles[1].save()

        warning_data = mock_data.warning_message.copy()
        warning_data["project_id"] = projects[0].pk
        warning = WarningMessage.objects.create(**warning_data)
        warning.publication_date = "2023-01-01T10:00:00+00:00"
        warning.save()

    def test_get_all(self):
        """Test get all news"""
        result = self.client.get(self.api_url, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 3)

    def test_get_limit_one(self):
        """Test limiting the result to one article"""
        result = self.client.get(self.api_url, {"limit": 1}, headers=self.api_headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 1)

    def test_invalid_limit(self):
        """Test passing invalid limit char"""
        result = self.client.get(
            self.api_url, {"limit": "1.1"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_get_articles_of_single_project(self):
        """Test get news from a single project"""
        first_project = Project.objects.first()

        result = self.client.get(
            self.api_url, {"project_ids": first_project.pk}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 2)

    def test_get_articles_of_multiple_projects(self):
        """Test get news from multiple projects"""
        first_project = Project.objects.first()
        last_project = Project.objects.last()

        result = self.client.get(
            self.api_url,
            {"project_ids": f"{first_project.pk},{last_project.pk}"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 3)

    def test_invalid_project_id(self):
        """Test passing invalid project id in comma seperated list"""
        result = self.client.get(
            self.api_url, {"project_ids": "1,foobar"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_article_content(self):
        """Test if content of article is as expected"""
        result = self.client.get(
            self.api_url,
            {"sort_by": "publication_date", "sort_order": "desc"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        article = Article.objects.order_by("-publication_date").first()

        expected_data = {
            "title": article.title,
            "publication_date": article.publication_date,
            "meta_id": {
                "type": "article",
                "id": article.pk,
            },
            "images": [],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_article_content_with_image(self):
        """Test if content of article with image is as expected"""
        image_data = {
            "id": 123,
            "sources": [
                {
                    "uri": "/foo/bar.png",
                    "width": 100,
                    "height": 50,
                },
            ],
            "aspectRatio": 2.0,
            "alternativeText": None,
        }

        article_data = mock_data.articles[0].copy()
        article_data["foreign_id"] = 9999
        article = Article.objects.create(**article_data)
        image = baker.make(
            ArticleImage, parent=article, alternativeText=None, aspectRatio=2.0, id=123
        )
        baker.make(
            ArticleImageSource, image=image, height=50, uri="/foo/bar.png", width=100
        )

        # Refresh from db to create datetime objects from datetime strings
        article.refresh_from_db()

        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 9999
        project = Project.objects.create(**project_data)

        article.projects.add(project)

        result = self.client.get(
            self.api_url, {"project_ids": [project.pk]}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        expected_data = {
            "title": article.title,
            "publication_date": article.publication_date,
            "meta_id": {
                "type": "article",
                "id": article.pk,
            },
            "images": [image_data],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_warning_content(self):
        """Test if content of warning is as expected"""
        result = self.client.get(
            self.api_url,
            {"sort_by": "publication_date", "sort_order": "asc"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        warning = WarningMessage.objects.first()

        expected_data = {
            # "type": "warning",
            "title": warning.title,
            "publication_date": warning.publication_date,
            "meta_id": {
                "type": "warning",
                "id": warning.pk,
            },
            "images": [],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_warning_content_with_image(self):
        """Test if content of warning with image is as expected"""
        project_data = mock_data.projects[0].copy()
        project_data["foreign_id"] = 9999
        project = Project.objects.create(**project_data)

        warning_data = mock_data.warning_message.copy()
        warning_data["project_id"] = project.pk
        warning = WarningMessage.objects.create(**warning_data)
        warning.refresh_from_db()

        warning_image_data = {
            "warning_id": warning.pk,
        }
        warning_image = WarningImage.objects.create(**warning_image_data)

        image_data = mock_data.images[0].copy()
        image_data["image"] = create_image_file(
            join(ROOT_DIR, "construction_work/tests/image_data/small_image.png")
        )
        image = Image.objects.create(**image_data)
        warning_image.images.add(image)

        result = self.client.get(
            self.api_url, {"project_ids": project.pk}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 200)

        expected_data = {
            "title": warning.title,
            "publication_date": warning.publication_date,
            "meta_id": {
                "type": "warning",
                "id": warning.pk,
            },
            "images": [
                {
                    "id": warning_image.pk,
                    "sources": [
                        {
                            "uri": "http://testserver/construction-work/media/images/image.jpg",
                            "width": image.width,
                            "height": image.height,
                        }
                    ],
                }
            ],
        }
        self.assertDictEqual(result.data[0], expected_data)

    def test_sort_news_by_publication_date_descending(self):
        """Test getting news sorted by publication date descending"""
        articles = Article.objects.all()
        warnings = WarningMessage.objects.all()
        news = []
        news.extend(articles)
        news.extend(warnings)
        news_pub_dates = [x.publication_date for x in news]
        sorted_pub_dates = sorted(news_pub_dates, reverse=True)

        result = self.client.get(
            self.api_url,
            {"sort_by": "publication_date", "sort_order": "desc"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)

        result_pub_dates = [x["publication_date"] for x in result.data]

        self.assertEqual(result_pub_dates, sorted_pub_dates)

    def test_invalid_sort_key(self):
        """Test sorting news with invalid sort key"""
        result = self.client.get(
            self.api_url, {"sort_by": "foobar"}, headers=self.api_headers
        )
        self.assertEqual(result.status_code, 400)

    def test_invalid_sort_key_but_no_news(self):
        """Test sorting news with invalid sort key"""
        result = self.client.get(
            self.api_url,
            {"project_ids": "9999", "sort_by": "foobar"},
            headers=self.api_headers,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data), 0)
