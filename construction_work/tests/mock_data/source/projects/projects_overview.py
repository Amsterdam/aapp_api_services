from construction_work.tests.mock_data.source.projects import (
    project_when,
    project_with_news_view,
    project_with_work_view,
)

MOCK_RESPONSE = {
    "data": {
        "view": {
            "name": "all_content",
            "pagination": {
                "totalPages": 1,
                "previousPage": False,
                "nextPage": False,
                "enabled": True,
                "currentPage": 1,
            },
            "nodes": [
                project_with_news_view.MOCK_DATA,
                project_when.MOCK_DATA,
                project_with_work_view.MOCK_DATA,
            ],
            "itemsPerPage": 9999,
        }
    }
}
