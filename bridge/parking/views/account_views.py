import logging
from datetime import datetime, timedelta

import jwt
from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response
from uritemplate import URITemplate

from bridge.parking.auth import Role, check_user_role
from bridge.parking.exceptions import (
    SSPAccountBlocked,
    SSPAccountInactive,
    SSPBadCredentials,
    SSPBadPassword,
    SSPPermitNotFoundError,
    SSPResponseError,
)
from bridge.parking.serializers.account_serializers import (
    AccountDetailsResponseSerializer,
    AccountLoginRequestSerializer,
    AccountLoginResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint, SSPEndpointExternal
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator

logger = logging.getLogger(__name__)


class ParkingAccountLoginView(BaseSSPView):
    """
    Login to SSP API (via redirect)
    """

    serializer_class = AccountLoginRequestSerializer
    response_serializer_class = AccountLoginResponseSerializer
    scope_mapping = {
        "ROLE_VISITOR_SSP": "visitor",
        "ROLE_USER_SSP": "permitHolder",
    }

    @ssp_openapi_decorator(
        response_serializer_class=AccountLoginResponseSerializer,
        requires_access_token=False,
        exceptions=[
            SSPBadCredentials,
            SSPBadPassword,
            SSPAccountInactive,
            SSPAccountBlocked,
        ],
    )
    def post(self, request, *args, **kwargs):
        request_serializer = self.serializer_class(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        request_payload = {
            "username": request_serializer.validated_data["report_code"],
            "password": request_serializer.validated_data["pin"],
        }
        access_jwt, expiration_timestamp, scope_mapped = (
            self._get_internal_access_token(request_payload)
        )
        access_jwt_external = self._get_external_access_token(request_payload)
        access_jwt += "%AMSTERDAMAPP%" + access_jwt_external

        # Manually set the expiration for the token on 15 minutes
        expiration_timestamp = datetime.now() + timedelta(minutes=15)

        response_payload = {
            "access_token": access_jwt,
            "scope": scope_mapped,
            "access_token_expiration": expiration_timestamp,
            "version": 2,
        }
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def _get_internal_access_token(self, request_payload):
        response_data = async_to_sync(self.ssp_api_call)(
            method="POST",
            endpoint=SSPEndpoint.LOGIN.value,
            body_data=request_payload,
            requires_access_token=False,
        )
        access_jwt = response_data.get("token")
        if not access_jwt:
            raise SSPResponseError("No token in SSP response")
        expiration_timestamp, scope_mapped = self._unpack_token(access_jwt)
        return access_jwt, expiration_timestamp, scope_mapped

    def _unpack_token(self, access_jwt):
        decoded_jwt = jwt.decode(access_jwt, options={"verify_signature": False})
        expiration_timestamp = datetime.fromtimestamp(decoded_jwt["exp"])
        try:
            scope = decoded_jwt["roles"][0]
            scope_mapped = self.scope_mapping[scope]
        except KeyError:
            logger.warning(f"Unknown SSP scope: {decoded_jwt.get('roles', '')}")
            scope_mapped = "unknown"
        return expiration_timestamp, scope_mapped

    def _get_external_access_token(self, request_payload):
        response_data = async_to_sync(self.ssp_api_call)(
            method="POST",
            endpoint=SSPEndpointExternal.LOGIN.value,
            body_data=request_payload,
            external_api=True,
            requires_access_token=False,
        )
        access_jwt = response_data.get("token")
        if not access_jwt:
            raise SSPResponseError("No token in SSP response")
        return access_jwt


class ParkingAccountDetailsView(BaseSSPView):
    """
    Get account details from SSP API
    """

    response_serializer_class = AccountDetailsResponseSerializer
    permit_types_with_balance = ["visitor"]

    @check_user_role(allowed_roles=[Role.USER.value, Role.VISITOR.value])
    @ssp_openapi_decorator(
        response_serializer_class=AccountDetailsResponseSerializer,
        exceptions=[SSPPermitNotFoundError],
    )
    def get(self, request, *args, **kwargs):
        # check if user is visitor or permit holder
        is_visitor = kwargs.get("is_visitor", False)
        if is_visitor:
            return self.make_response(
                {
                    "wallet": {
                        "balance": 0.0,
                        "currency": "EUR",
                    }
                }
            )

        response_data = async_to_sync(self.ssp_api_call)(
            method="GET",
            endpoint=SSPEndpoint.PERMITS.value,
            query_params={"page": 1, "row_per_page": 250},
        )
        permits = response_data["data"]
        permits = [
            p
            for p in permits
            if p["status"] != "control"
            and p["permit_type"] in self.permit_types_with_balance
        ]
        if permits:
            url_template = SSPEndpoint.PERMIT.value
            url = URITemplate(url_template).expand(permit_id=permits[0]["id"])
            response_data = async_to_sync(self.ssp_api_call)(
                method="GET",
                endpoint=url,
            )
            balance_in_cents = response_data["ssp"]["main_account"]["money_balance"]
            balance = (balance_in_cents or 0.0) / 100
        else:
            balance = None

        return self.make_response(
            {
                "wallet": {
                    "balance": balance,
                    "currency": "EUR",
                }
            }
        )

    def make_response(self, response_payload):
        response_serializer = self.response_serializer_class(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
