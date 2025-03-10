import pathlib
from io import BytesIO
from os.path import join

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]

SCALED_IMAGE_FORMAT = "JPEG"
RESOLUTIONS = {
    "small": (320, 180),
    "medium": (768, 432),
    "large": (1280, 720),
}


def scale_image(image_file) -> dict[str, BytesIO]:
    pil_image = PILImage.open(image_file)

    scaled_images = {}
    for key, size in RESOLUTIONS.items():
        pil_image_resized = pil_image.copy()
        pil_image_resized.thumbnail(size, PILImage.Resampling.LANCZOS)

        img_io = BytesIO()
        pil_image_resized = pil_image_resized.convert("RGB")
        pil_image_resized.save(img_io, format=SCALED_IMAGE_FORMAT)
        img_io.seek(0)
        scaled_images[key] = img_io
    return scaled_images


def get_example_image_file(
    file_path: str = "core/tests/example.jpg",
) -> SimpleUploadedFile:
    filepath = join(ROOT_DIR, file_path)
    with open(filepath, "rb") as image_file:
        file = SimpleUploadedFile(
            name=file_path.split("/")[-1], content=image_file.read()
        )
    return file
