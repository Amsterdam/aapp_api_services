import requests
from django.conf import settings


class ImageSetService:
    def __init__(self):
        self.data = None

    def get(self, image_set_id):
        base_url = settings.IMAGE_ENDPOINTS["DETAIL"]
        url = f"{base_url}/{image_set_id}"
        response = requests.get(url)
        response.raise_for_status()
        self.data = response.json()
        return self.data

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

        response = requests.post(image_upload_url, data=data, files=files)
        response.raise_for_status()
        self.data = response.json()
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
