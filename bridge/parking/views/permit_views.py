import json
import logging
import math
import re

import jwt
from rest_framework import status
from rest_framework.response import Response
from uritemplate import URITemplate

from bridge.parking.auth import Role, check_user_role, get_access_token
from bridge.parking.exceptions import SSPPermitNotFoundError
from bridge.parking.serializers.permit_serializer import (
    PaymentZoneSerializer,
    PermitGeoJSONSerializer,
    PermitItemSerializer,
    PermitsRequestSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint, SSPEndpointExternal
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator

logger = logging.getLogger(__name__)


class ParkingPermitsView(BaseSSPView):
    """
    Get permits from SSP API
    """

    serializer_class = PermitsRequestSerializer
    response_serializer_class = PermitItemSerializer
    ssp_endpoint = SSPEndpoint.PERMITS.value
    weekdays = [
        "Maandag",
        "Dinsdag",
        "Woensdag",
        "Donderdag",
        "Vrijdag",
        "Zaterdag",
        "Zondag",
    ]

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        serializer_as_params=PermitsRequestSerializer,
        response_serializer_class=PermitItemSerializer(many=True),
        exceptions=[SSPPermitNotFoundError],
    )
    def get(self, request, *args, **kwargs):
        # check role of user in jwt token
        is_visitor = kwargs.get("is_visitor", False)
        if is_visitor:
            ssp_access_token = get_access_token(self.request)
            decoded_jwt = jwt.decode(
                ssp_access_token, options={"verify_signature": False}
            )
            client_product_id = decoded_jwt.get("client_product_id", "")
            permits_data = [{"id": client_product_id}]
        else:
            permits_data = self.collect_all_pages()
            permits_data = [p for p in permits_data if p["status"] != "control"]

        for n, permit in enumerate(permits_data):
            permit_details = self.collect_permit_details(permit)
            permit_details["permit"]["mapped_type"] = self.get_mapped_permit_type(
                permit_details
            )
            permits_data[n]["details"] = permit_details

        filtered_permits = []
        for permit in permits_data:
            config = permit["details"]["config"]
            if config["can_start_parking_session"] or config["can_activate_vrn"]:
                filtered_permits.append(permit)
        permits_data = filtered_permits

        response_payload = [
            {
                "report_code": permit.get("id"),
                "time_balance": permit["details"]["ssp"][
                    "visitor_account" if is_visitor else "main_account"
                ]["time_balance"],  # always show main account?
                "parking_machine_favorite": permit["details"]["ssp"].get(
                    "favorite_machine_number"
                ),
                "time_valid_until": None
                if is_visitor
                else permit["details"]["ssp"]["time_balance_expires_at"],
                "permit_type": permit["details"]["permit"]["mapped_type"],
                "permit_name": permit["details"]["permit"]["name"],
                "permit_zone": {
                    "permit_zone_id": permit["details"]["permit"]["zone"],
                    "name": permit["details"]["permit"]["zone"],
                    "description": None
                    if is_visitor
                    else permit.get("permit_description"),
                }
                if permit["details"]["permit"]["zone"]
                else None,
                "payment_zones": [
                    {
                        "id": zone.get("zone_id"),
                        "description": zone.get("zone_description"),
                        "city": "Amsterdam",  # DEPRECATED
                        "days": [
                            {
                                "day_of_week": self.weekdays[n],  # Guesswork!
                                "start_time": f"{day[0].get('startTime')[:2]}:{day[0].get('startTime')[2:]}",  # Take first time frame only??
                                "end_time": f"{day[0].get('endTime')[:2]}:{day[0].get('endTime')[2:]}",  # Take first time frame only??
                            }
                            for n, day in enumerate(zone["time_frame_data"])
                        ],
                    }
                    for zone in permit.get("payment_zones", [])
                ],
                "visitor_account": {
                    "report_code": permit["details"]["ssp"]["visitor_account"][
                        "username"
                    ],
                    "pin": permit["details"]["ssp"]["visitor_account"]["pin"],
                    "seconds_remaining": permit["details"]["ssp"]["visitor_account"][
                        "time_balance"
                    ],
                }
                if permit["details"]["ssp"]["visitor_account"]["username"]
                else None,
                "parking_rate": {
                    "value": (permit["details"]["permit"]["cost"] or 0) / 100,
                    "currency": "EUR",  # DEPRECATED
                },
                "parking_rate_original": {
                    "value": None,  # DEPRECATED
                    "currency": "EUR",  # DEPRECATED
                },
                "time_balance_applicable": permit["details"]["config"][
                    "has_time_balance"
                ],
                "money_balance_applicable": permit["details"]["config"][
                    "has_money_balance"
                ],
                "forced_license_plate_list": permit["details"]["config"][
                    "can_input_vrn"
                ],
                "no_endtime": self.get_no_end_time(permit),
                "visitor_account_allowed": permit["details"]["config"][
                    "has_visitor_account"
                ],
                "max_session_length_in_days": self.get_max_session_length(permit),
                "can_select_zone": permit["details"]["config"]["can_select_zone"],
            }
            for permit in permits_data
        ]
        response_serializer = self.response_serializer_class(
            many=True, data=response_payload
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def get_mapped_permit_type(self, permit_details):
        permit_type_mapping = {
            "business": "Codevergunning",
            "resident": "Mantelzorgvergunning",
            "visitor": "Bezoekersvergunning",
        }
        permit_type = permit_details["permit"]["type"]
        permit_name = permit_details["permit"]["name"]
        mapped_type = permit_type_mapping.get(permit_type, "Onbekend")
        if permit_type == "handicap":
            if permit_name == "GA-parkeervergunning voor bewoners (passagiers)":
                mapped_type = "GA-parkeervergunning voor bewoners (passagiers)"
            elif permit_name == "GA-parkeervergunning voor bezoekers (passagiers)":
                mapped_type = "GA-bezoekerskaart"
            # Unmapped types as of now (will go to "Onbekend"):
            # - GA-parkeervergunning voor bewoners (bestuurders)
            # - GA-parkeervergunning voor bezoekers (bestuurders)
        return mapped_type

    def collect_all_pages(self):
        total_pages, page_count = 1, 0
        permits_data = []
        while page_count < total_pages:
            page_count += 1
            data = {
                "page": page_count,
                "row_per_page": 250,
            }
            response = self.ssp_api_call(
                method="GET",
                endpoint=self.ssp_endpoint,
                query_params=data,
            )
            response_data = response.data
            total_pages = math.ceil(response_data["count"] / data["row_per_page"])
            permits_data += response_data["data"]
        return permits_data

    def collect_permit_details(self, permit):
        url_template = SSPEndpoint.PERMIT.value
        url = URITemplate(url_template).expand(permit_id=permit["id"])
        response = self.ssp_api_call(
            method="GET",
            endpoint=url,
        )
        return response.data

    def get_no_end_time(self, permit):
        return permit["details"]["config"]["can_activate_vrn"]

    def get_max_session_length(self, permit):
        no_end_time = self.get_no_end_time(permit)
        if no_end_time:
            return 0
        if permit.get("permit_type") == "business":
            return 28
        return 1


class ParkingPermitZoneView(BaseSSPView):
    """
    Get permits from SSP API
    """

    response_serializer_class = PermitGeoJSONSerializer
    ssp_endpoint = SSPEndpoint.PERMITS.value

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=PermitGeoJSONSerializer,
        exceptions=[SSPPermitNotFoundError],
    )
    def get(self, request, *args, **kwargs):
        permit_id = kwargs.get("permit_id")
        url_template = SSPEndpoint.PERMIT.value
        url = URITemplate(url_template).expand(permit_id=permit_id)
        response = self.ssp_api_call(
            method="GET",
            endpoint=url,
        )

        # geo_json field can be None, change it to empty dictionary, otherwise json loads fails
        if response.data["permit"]["geo_json"] is None:
            response.data["permit"]["geo_json"] = "{}"

        response_payload = {
            "geojson": json.loads(response.data["permit"]["geo_json"]),
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )


class ParkingPermitZoneByMachineView(BaseSSPView):
    """
    Get permits from SSP API
    """

    response_serializer_class = PaymentZoneSerializer
    weekdays = [
        "Maandag",
        "Dinsdag",
        "Woensdag",
        "Donderdag",
        "Vrijdag",
        "Zaterdag",
        "Zondag",
    ]
    ssp_endpoint = SSPEndpointExternal.PARKING_ZONE_BY_MACHINE.value

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=PaymentZoneSerializer,
        exceptions=[SSPPermitNotFoundError],
    )
    def get(self, request, *args, **kwargs):
        permit_id = kwargs.get("permit_id")
        parking_machine = kwargs.get("parking_machine_id")
        response = self.ssp_api_call(
            method="POST",
            endpoint=self.ssp_endpoint,
            body_data={
                "machine_number": int(parking_machine),
                "client_product_id": int(permit_id),
            },
            external_api=True,
            wrap_body_data_with_token=True,
        )

        zone = response.data["data"]

        # extract hourly rate from zone description
        hourly_rate = re.search(r"€\s*\d{1,2},\d{2}", zone.get("zone_description"))

        response_payload = {
            "id": zone.get("zone_id"),
            "description": zone.get("zone_description"),
            "hourly_rate": hourly_rate.group(0) if hourly_rate else None,
            "city": "Amsterdam",  # DEPRECATED
            "days": [
                {
                    "day_of_week": self.weekdays[n],  # Guesswork!
                    "start_time": f"{day[0].get('startTime')[:2]}:{day[0].get('startTime')[2:]}",  # Take first time frame only??
                    "end_time": f"{day[0].get('endTime')[:2]}:{day[0].get('endTime')[2:]}",  # Take first time frame only??
                }
                for n, day in enumerate(zone["time_frame_data"])
            ],
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
