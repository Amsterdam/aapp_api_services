from typing import Dict


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
