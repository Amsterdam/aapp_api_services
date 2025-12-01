from core.exceptions import ApiKeyInvalidException
from core.utils.coordinates_utils import wgs_to_rd
from core.utils.openapi_utils import custom_extend_schema


def calculate_bbox_from_wsg_coordinates(lon: float, lat: float) -> dict[str, float]:
    """
    Calculates small box around given coordinates in Rijksdriehoek values.
    """
    # convert coordinates to rijksdriehoek coordinates
    address_rd_x, address_rd_y = wgs_to_rd(lon, lat)

    return {
        "min_x": address_rd_x - 100,
        "min_y": address_rd_y - 100,
        "max_x": address_rd_x + 100,
        "max_y": address_rd_y + 100,
    }


def extend_schema_for_burning_guide(
    success_response=None, exceptions=None, serializer_as_params=None, **kwargs
):
    additional_params = []
    if serializer_as_params:
        additional_params.append(serializer_as_params)

    return custom_extend_schema(
        default_exceptions=[ApiKeyInvalidException],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=additional_params,
        **kwargs,
    )
