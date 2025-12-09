from core.exceptions import ApiKeyInvalidException
from core.utils.coordinates_utils import wgs_to_rd
from core.utils.openapi_utils import custom_extend_schema


def calculate_rd_bbox_from_wsg_coordinates(lon: float, lat: float) -> dict[str, float]:
    """
    Given WGS84 coordinates (longitude, latitude), calculate a bounding box in Rijksdriehoek coordinates.
    The bounding box is defined as a square of 200m x 200m centered around the given point.

    Args:
        lon (float): Longitude in decimal degrees.
        lat (float): Latitude in decimal degrees.

    Returns:
        tuple: A tuple representing the bounding box in Rijksdriehoek coordinates
               (min_x, min_y, max_x, max_y).
    """
    center_x, center_y = wgs_to_rd(lon, lat)
    half_size = 100  # 100 meters in each direction to make a 200m x 200m box

    return {
        "min_x": center_x - half_size,
        "min_y": center_y - half_size,
        "max_x": center_x + half_size,
        "max_y": center_y + half_size,
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
