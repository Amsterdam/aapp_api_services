from typing import Type

from django.db.models import Prefetch
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from construction_work.models.manage_models import Image, WarningImage
from construction_work.models.project_models import Project
from construction_work.utils.model_utils import get_start_end_date_for_max_age


def get_recent_articles_of_project(
    project: Project,
    article_max_age: int,
    article_serializer_class: Type[ModelSerializer],
) -> list:
    """Get articles for a single project limited to max age"""
    start_date, end_date = get_start_end_date_for_max_age(article_max_age)

    articles = project.article_set.filter(
        publication_date__range=[start_date, end_date]
    ).all()
    article_serializer = article_serializer_class(articles, many=True)
    return article_serializer.data


def get_recent_warnings_of_project(
    project: Project,
    article_max_age: int,
    warning_serializer_class: Type[ModelSerializer],
    context: dict = None,
) -> list:
    """Get articles for a single project limited to max age"""
    start_date, end_date = get_start_end_date_for_max_age(article_max_age)

    warning_messages = project.warningmessage_set.filter(
        publication_date__range=[start_date, end_date]
    ).all()
    warning_message_serializer = warning_serializer_class(
        warning_messages, many=True, context=context
    )
    return warning_message_serializer.data


def get_warningimage_width_height_prefetch():
    return Prefetch(
        "warningimage_set",
        queryset=WarningImage.objects.prefetch_related(
            Prefetch("image_set", queryset=Image.objects.only("width", "height"))
        ),
    )


def get_model_fields_from_serializer(serializer_class):
    """
    Get all model fields from a serializer, excluding SerializerMethodFields.
    Always includes the 'id' field for prefetch operations.

    Args:
        serializer_class: The serializer class to inspect

    Returns:
        set: Set of field names to be used with .only()
    """
    # Get fields from serializer's Meta class
    serializer_fields = serializer_class.Meta.fields

    # Get all SerializerMethodField names from the serializer
    method_fields = {
        field_name
        for field_name, field in serializer_class._declared_fields.items()
        if isinstance(field, serializers.SerializerMethodField)
    }

    # Always include 'id' field for prefetch to work
    return {"id"}.union(
        field for field in serializer_fields if field not in method_fields
    )
