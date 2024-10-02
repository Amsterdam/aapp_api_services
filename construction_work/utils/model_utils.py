from datetime import datetime, timedelta
from typing import Dict, Type

from rest_framework.serializers import ModelSerializer


def create_id_dict(model_instance) -> Dict[str, str]:
    """
    Create a dictionary with 'id' and 'type' based on the model instance.

    Args:
        model_instance: An instance of a Django model.

    Returns:
        Dict[str, str]: A dictionary containing 'id' and optionally 'type'.
    """
    from construction_work.models import Article, WarningMessage

    model_type = type(model_instance)
    type_name = None
    if model_type == Article:
        type_name = "article"
    elif model_type == WarningMessage:
        type_name = "warning"

    id_dict = {"id": str(model_instance.pk)}
    if type_name:
        id_dict["type"] = type_name

    return id_dict


def get_start_end_date_for_max_age(max_age: int):
    datetime_now = datetime.now().astimezone()
    start_date = datetime_now - timedelta(days=max_age)
    end_date = datetime_now + timedelta(days=1)
    return start_date, end_date


def get_recent_articles_of_project(
    project,
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


def get_recent_articles_of_project(
    project,
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
    project,
    article_max_age: int,
    warning_serializer_class: Type[ModelSerializer],
    context: dict = {},
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


def get_recent_articles_and_warnings_of_project(
    project,
    article_max_age: int,
    article_serializer_class: Type[ModelSerializer],
    warning_serializer_class: Type[ModelSerializer],
    context: dict = {},
) -> list:
    """Combine articles and warning for a single project limited to max age"""
    all_items = []

    articles = get_recent_articles_of_project(
        project, article_max_age, article_serializer_class
    )
    all_items.extend(articles)

    warnings = get_recent_warnings_of_project(
        project, article_max_age, warning_serializer_class, context
    )
    all_items.extend(warnings)

    return all_items
