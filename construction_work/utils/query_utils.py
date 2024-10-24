from typing import Type

from django.db.models import Prefetch
from rest_framework.serializers import ModelSerializer

from construction_work.models import Image, Project, WarningImage
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
            Prefetch("images", queryset=Image.objects.only("width", "height"))
        ),
    )
