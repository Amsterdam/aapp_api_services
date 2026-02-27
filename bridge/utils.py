import requests
import shapely
from django.conf import settings
from rest_framework import serializers

from core.utils.caching_utils import cache_function


def validate_digits(variable_name: str, value: str) -> str:
    # check that variable contains only digits
    if not value.isdigit():
        raise serializers.ValidationError(
            {variable_name: f"{variable_name} must contain only digits."}
        )
    return value


@cache_function(timeout=60 * 60 * 24)  # Cache for 24 hours
def load_postal_area_shapes():
    """
    Function to load the postal data:
    - make request to amsterdam maps data
    - for each postal code:
        - save shape to dict
    """
    url = settings.BURNING_GUIDE_AMSTERDAM_MAPS_URL
    params = {"KAARTLAAG": "PC4_BUURTEN", "THEMA": "postcode"}
    response = requests.get(url, params=params)

    response.raise_for_status()
    data_json = response.json()
    postal_codes_raw = data_json["features"]

    final_dict = {}
    for postal_code_features in postal_codes_raw:
        # get postal code and geometry
        postal_code = postal_code_features["properties"]["Postcode4"]
        polygon_object = shapely.geometry.shape(postal_code_features["geometry"])

        # add polygon_object to final dict
        final_dict[postal_code] = polygon_object

    return final_dict
