""" Mock data for unittests
"""


class TestData:
    """Testdata used in unittests"""

    def __init__(self):
        self.modules = [
            {"slug": "slug0", "status": 1},
            {"slug": "slug1", "status": 1},
            {"slug": "slug2", "status": 1},
            {"slug": "slug3", "status": 1},
            {"slug": "slug4", "status": 1},
            {"slug": "slug5", "status": 1},
        ]

        self.module_versions = [
            {
                "module": None,
                "title": "title",
                "icon": "icon",
                "version": "1.2.3",
                "description": "description",
            },
            {
                "module": None,
                "title": "title",
                "icon": "icon",
                "version": "1.2.20",
                "description": "description",
            },
            {
                "module": None,
                "title": "title",
                "icon": "icon",
                "version": "1.3.4",
                "description": "description",
            },
            {
                "module": None,
                "title": "title",
                "icon": "icon",
                "version": "1.30.4",
                "description": "description",
            },
            {
                "module": None,
                "title": "title",
                "icon": "icon",
                "version": "2.10.2",
                "description": "description",
            },
            {
                "module": None,
                "title": "title",
                "icon": "icon",
                "version": "10.3.2",
                "description": "description",
            },
        ]

        self.modules_by_app = [
            {
                "releaseVersion": "0.0.1",
                "moduleSlug": "slug0",
                "moduleVersion": "1.2.3",
                "status": 1,
            },
            {
                "releaseVersion": "0.0.2",
                "moduleSlug": "slug0",
                "moduleVersion": "1.2.3",
                "status": 1,
            },
            {
                "releaseVersion": "0.1.1",
                "moduleSlug": "slug0",
                "moduleVersion": "1.2.20",
                "status": 1,
            },
            {
                "releaseVersion": "0.0.1",
                "moduleSlug": "slug1",
                "moduleVersion": "1.3.4",
                "status": 0,
            },
            {
                "releaseVersion": "0.0.1",
                "moduleSlug": "slug2",
                "moduleVersion": "1.30.4",
                "status": 1,
            },
            {
                "releaseVersion": "0.0.1",
                "moduleSlug": "slug3",
                "moduleVersion": "2.10.2",
                "status": 1,
            },
            {
                "releaseVersion": "0.0.0",
                "moduleSlug": "slug4",
                "moduleVersion": "10.3.2",
                "status": 1,
            },
        ]

        self.module_order = [
            {"releaseVersion": "0.0.0", "order": ["slug0"]},
            {"releaseVersion": "0.0.1", "order": ["slug0", "slug1", "slug2"]},
        ]

        self.releases = [
            {
                "version": "0.0.0",
                "release_notes": "release 0.0.0",
                "published": "1970-01-01",
                "unpublished": "1970-12-31",
                "created": "1970-01-01",
                "modified": None,
                "module_order": ["slug4"],
            },
            {
                "version": "0.0.1",
                "release_notes": "release 0.0.1",
                "published": "1971-01-01",
                "unpublished": "1971-12-31",
                "created": "1970-01-01",
                "modified": None,
                "module_order": ["slug0", "slug1", "slug2", "slug3"],
            },
            {
                "version": "0.0.2",
                "release_notes": "release 0.0.2",
                "published": "1971-01-01",
                "unpublished": "1971-12-31",
                "created": "1970-01-01",
                "modified": None,
                "module_order": ["slug0"],
            },
            {
                "version": "0.1.1",
                "release_notes": "release 0.1.1",
                "published": "1971-01-01",
                "unpublished": "1971-12-31",
                "created": "1970-01-01",
                "modified": None,
                "module_order": ["slug0"],
            },
        ]
