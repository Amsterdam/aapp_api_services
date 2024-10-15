from django.core.files.uploadedfile import SimpleUploadedFile


def create_image_file(image_path):
    with open(image_path, "rb") as image_file:
        image_file = SimpleUploadedFile(
            name="image.jpg",
            content=image_file.read(),
            content_type="image/jpeg",
        )
    return image_file
