"""
Mock data that is the output of the extraction process.
It can be used as an input for testing the transformation of projects and articles
DO NOT USE IT AS INPUT FOR THE EXTRACTION STEP
"""

from construction_work.tests.mock_data.source.articles import (
    news_article_view,
    work_article_view,
)
from construction_work.tests.mock_data.source.projects import projects_overview

MOCK_DATA = {
    "projects": projects_overview.MOCK_RESPONSE["data"]["view"]["nodes"],
    "news_articles": {
        79631: news_article_view.MOCK_RESPONSE_79631["data"]["view"]["nodes"],
        79932: news_article_view.MOCK_RESPONSE_79932["data"]["view"]["nodes"],
        79592: news_article_view.MOCK_RESPONSE_79592["data"]["view"]["nodes"],
    },
    "work_articles": {
        79593: work_article_view.MOCK_RESPONSE["data"]["view"]["nodes"],
    },
}
