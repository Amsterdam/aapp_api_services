import logging

import requests
from django.conf import settings
from django.core.cache import cache

from core.services.internal_http_client import InternalServiceSession

logger = logging.getLogger(__name__)


class ImageSetService:
    def __init__(self):
        self.data = None
        self.client = InternalServiceSession()

    def get(self, image_set_id):
        cache_key = f"{__name__}.get_from_id.{image_set_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            self.data = cached_data
            return self.data

        base_url = settings.IMAGE_ENDPOINTS["DETAIL"]
        url = f"{base_url}/{image_set_id}"
        response = self.client.get(url)
        response.raise_for_status()
        self.data = response.json()
        cache.set(cache_key, self.data, timeout=60 * 60 * 24)
        return self.data

    def exists(self, image_set_id):
        try:
            self.get(image_set_id)
            return True
        except requests.exceptions.HTTPError:
            return False

    def upload(self, image, description=None):
        image_upload_url = settings.IMAGE_ENDPOINTS["POST_IMAGE"]
        files = {"image": image}
        data = (
            {
                "description": description,
            }
            if description
            else {}
        )

        response = self.client.post(image_upload_url, data=data, files=files)
        response.raise_for_status()
        self.data = response.json()
        return self.data

    def get_or_upload_from_url(self, url, description=None):
        """
        If the image already exists, it will be returned.
        If the image does not exist, it will be uploaded and then returned.
        """
        cache_key = f"{__name__}.get_from_url.{url}"
        cached_data = cache.get(cache_key)
        if cached_data:
            self.data = cached_data
            return self.data

        image_upload_url = settings.IMAGE_ENDPOINTS["POST_IMAGE_FROM_URL"]
        data = {
            "url": url,
            "description": description,
        }
        response = self.client.post(image_upload_url, data=data)
        response.raise_for_status()
        self.data = response.json()
        cache.set(cache_key, self.data, timeout=60 * 60 * 24)
        return self.data

    @property
    def url_small(self):
        return self.data["variants"][0]["image"]

    @property
    def url_medium(self):
        return self.data["variants"][1]["image"]

    @property
    def url_large(self):
        return self.data["variants"][2]["image"]

    def json(self):
        return self.data
