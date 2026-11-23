import hashlib
import io
import logging
import uuid

import requests
from django.core.files.base import ContentFile
from django.db import IntegrityError, connection, transaction
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

from core.utils.image_utils import SCALED_IMAGE_FORMAT, scale_image
from image.models import ImageSet, ImageVariant

logger = logging.getLogger(__name__)


def create_set(image_file, validated_data, stored_files=None):
    owns_file_tracking = stored_files is None
    stored_files = stored_files if stored_files is not None else []
    try:
        with transaction.atomic():
            scaled = scale_image(image_file)
            variants = {}
            for size in ("small", "medium", "large"):
                variant = ImageVariant()
                filename = f"{size}-{uuid.uuid4()}.{SCALED_IMAGE_FORMAT}"
                variant.image.save(
                    filename, ContentFile(scaled[size].read()), save=False
                )
                stored_files.append((variant.image.storage, variant.image.name))
                variant.save()
                variants[f"image_{size}"] = variant
            return ImageSet.objects.create(**variants, **validated_data)
    except Exception:
        if owns_file_tracking:
            _cleanup_stored_files(stored_files)
        raise


def create_from_upload(image_file, validated_data):
    try:
        return create_set(image_file, validated_data)
    except IntegrityError:
        identifier = validated_data.get("identifier")
        if (
            identifier is not None
            and ImageSet.objects.filter(identifier=identifier).exists()
        ):
            raise ValidationError(
                {
                    "identifier": [
                        "Er bestaat al een image set met eenzelfde identifier."
                    ]
                }
            )
        raise


def create_from_url(url, validated_data):
    identifier = hashlib.sha256(url.encode("utf-8")).hexdigest()
    stored_files = []
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))", [identifier]
                )
            image_set = ImageSet.objects.filter(identifier=identifier).first()
            if image_set:
                return image_set
            image_file = retrieve_image(url)
            return create_set(
                image_file,
                {**validated_data, "identifier": identifier},
                stored_files,
            )
    except IntegrityError:
        _cleanup_stored_files(stored_files)
        image_set = ImageSet.objects.filter(identifier=identifier).first()
        if image_set:
            return image_set
        raise
    except Exception:
        _cleanup_stored_files(stored_files)
        raise


def _cleanup_stored_files(stored_files):
    for storage, name in stored_files:
        try:
            if ImageVariant.objects.filter(image=name).exists():
                continue
            storage.delete(name)
        except Exception:
            logger.exception("Failed deleting rolled-back image file %s", name)


def retrieve_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as error:
        raise ValidationError(f"Failed creating image set from URL: {error}")
    image_file = io.BytesIO(response.content)
    try:
        Image.open(image_file).verify()
        image_file.seek(0)
    except UnidentifiedImageError:
        raise ValidationError("Provided URL does not contain a valid image.")
    return image_file
