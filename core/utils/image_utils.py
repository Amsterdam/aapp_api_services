from io import BytesIO

from PIL import Image as PILImage

SCALED_IMAGE_FORMAT = "JPEG"


def scale_image(
    image_file, resolutions: dict[str, tuple[int, int]]
) -> dict[str, BytesIO]:
    pil_image = PILImage.open(image_file)

    scaled_images = {}
    for key, size in resolutions.items():
        pil_image_resized = pil_image.copy()
        pil_image_resized.thumbnail(size, PILImage.Resampling.LANCZOS)

        img_io = BytesIO()
        pil_image_resized = pil_image_resized.convert("RGB")
        pil_image_resized.save(img_io, format=SCALED_IMAGE_FORMAT)
        img_io.seek(0)
        scaled_images[key] = img_io
    return scaled_images
