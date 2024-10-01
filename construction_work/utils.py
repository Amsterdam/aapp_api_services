import json
import urllib.parse

import geopy.distance
import requests
from django.conf import settings


def create_id_dict(model_type, _id):
    """Create a dict with id and object type"""
    from construction_work.models import Article, WarningMessage

    type_name = None
    if model_type == Article:
        type_name = "article"
    elif model_type == WarningMessage:
        type_name = "warning"

    if type_name is None:
        return {"id": _id}

    return {"id": _id, "type": type_name}


def get_distance(coords_1, coords_2):
    """Get distance"""
    meter = None

    if not any(
        elem is None for elem in [coords_1[0], coords_1[1], coords_2[0], coords_2[1]]
    ):
        try:
            meter = int(geopy.distance.geodesic(coords_1, coords_2).km * 1000)
        except ValueError:
            pass
        except Exception as error:
            print(error, flush=True)

    return meter


def address_to_gps(address):
    """Convert address to GPS info via API call"""
    url = f"{settings.ADDRESS_TO_GPS_API}{urllib.parse.quote_plus(address)}"
    result = requests.get(url=url, timeout=1)
    data = json.loads(result.content)
    if len(data["results"]) == 1:
        lon = data["results"][0]["centroid"][0]
        lat = data["results"][0]["centroid"][1]
        return lat, lon
    return None, None
