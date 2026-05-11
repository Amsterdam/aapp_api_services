import logging
from urllib.parse import urljoin

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from news.enums.news_article import NewsArticle
from news.etl.extract_data import IproxFetcher

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/amsterdam/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "item/")
NEWS_ARTICLE_TYPES = NewsArticle.choices_as_list()

iprox_fetcher = IproxFetcher(
    iprox_fetch_url=IPROX_URL,
    iprox_detail_url=IPROX_ARTICLES_URL,
    sources=NEWS_ARTICLE_TYPES,
    max_concurrent_requests=20,
)


class DataLoadView(APIView):
    def get(self, request, *args, **kwargs):
        """Temporary view to call extract step"""
        extracted_data = iprox_fetcher.extract()
        if not extracted_data:
            logger.info("No new or altered news articles found. Ending ETL process.")
            return Response(
                {"message": "No new or altered news articles found."},
                status=status.HTTP_200_OK,
            )

        logger.info(
            f"Now we continue with the transform and load steps for {len(extracted_data)} news articles."
        )
        return Response({"message": "Extract step called"}, status=status.HTTP_200_OK)
