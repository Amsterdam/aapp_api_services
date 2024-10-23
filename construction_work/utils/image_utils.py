import base64
from io import BytesIO
from typing import List, Tuple

from PIL import Image as PILImage

RESOLUTIONS = {
    "small": (320, 180),
    "medium": (768, 432),
    "large": (1280, 720),
}

SCALED_IMAGE_FORMAT = "JPEG"


def scale_image(image_file) -> List[Tuple[str, BytesIO]]:
    pil_image = PILImage.open(image_file)

    scaled_images = []

    for key, size in RESOLUTIONS.items():
        pil_image_resized = pil_image.copy()
        pil_image_resized.thumbnail(size, PILImage.Resampling.LANCZOS)

        img_io = BytesIO()
        pil_image_resized = pil_image_resized.convert("RGB")
        pil_image_resized.save(img_io, format=SCALED_IMAGE_FORMAT)
        img_io.seek(0)
        scaled_images.append((key, img_io))

    return scaled_images


def create_image_data(image_path):
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
    return image_data
