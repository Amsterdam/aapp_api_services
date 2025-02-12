import requests
from django.conf import settings


class ImageSetService:
    def __init__(self, image_set_id):
        base_url = settings.IMAGE_ENDPOINTS["DETAIL"]
        url = f"{base_url}/{image_set_id}"
        response = requests.get(url)
        self.data = response.json()

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
