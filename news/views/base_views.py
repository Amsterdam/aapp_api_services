import logging
from urllib.parse import urljoin

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from news.enums.news_article import NewsArticle
from news.etl.extract_data import IproxFetcher

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "list/amsterdam/")
IPROX_DETAIL_URL = urljoin(IPROX_URL, "item/")
NEWS_ARTICLE_TYPES = NewsArticle.choices_as_list()

iprox_fetcher = IproxFetcher(
    iprox_fetch_url=IPROX_ARTICLES_URL,
    iprox_detail_url=IPROX_DETAIL_URL,
    sources=NEWS_ARTICLE_TYPES,
    max_concurrent_requests=20,
)


class DataLoadView(APIView):
    def get(self, request, *args, **kwargs):
        """Temporary view to call extract step"""
        extracted_data = iprox_fetcher.extract()
        if not extracted_data:
            logger.info("No articles found. Ending ETL process.")
            return Response(
                {"message": "No articles found."},
                status=status.HTTP_200_OK,
            )

        logger.info(
            f"Now we continue with the transform and load steps for {len(extracted_data)} news articles."
        )
        return Response({"data": extracted_data}, status=status.HTTP_200_OK)
