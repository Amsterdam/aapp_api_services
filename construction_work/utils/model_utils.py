from datetime import datetime, timedelta
from typing import Dict


def create_id_dict(model_instance) -> Dict[str, str]:
    from construction_work.models.article_models import Article
    from construction_work.models.manage_models import WarningMessage

    """
    Create a dictionary with 'id' and 'type' based on the model instance.

    Args:
        model_instance: An instance of a Django model.

    Returns:
        Dict[str, str]: A dictionary containing 'id' and 'type'.
    """
    if isinstance(model_instance, Article):
        type_name = "article"
    elif isinstance(model_instance, WarningMessage):
        type_name = "warning"
    else:
        type_name = model_instance.__class__.__name__.lower()

    return {"id": model_instance.pk, "type": type_name}


def get_start_end_date_for_max_age(max_age: int):
    datetime_now = datetime.now().astimezone()
    start_date = datetime_now - timedelta(days=max_age)
    return start_date, datetime_now
