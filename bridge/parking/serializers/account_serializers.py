from rest_framework import serializers

from bridge.parking.exceptions import SSPPinCodeCheckError
from bridge.parking.serializers.general_serializers import (
    AmountCurrencySerializer,
    RedirectSerializer,
)
from core.utils.serializer_utils import (
    CamelToSnakeCaseSerializer,
    SnakeToCamelCaseSerializer,
)


class AccountLoginRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    pin = serializers.CharField()


class AccountLoginResponseSerializer(CamelToSnakeCaseSerializer):
    access_token = serializers.CharField()
    scope = serializers.CharField()


class PinCodeRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    phone_number = serializers.CharField()


class PinCodeChangeRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    pin_current = serializers.CharField()
    pin_code = serializers.CharField()
    pin_code_check = serializers.CharField()

    def validate_pin_code_check(self, value):
        if self.initial_data.get("pin_code") != value:
            raise SSPPinCodeCheckError
        return value


class PinCodeResponseSerializer(CamelToSnakeCaseSerializer):
    pass


class AddressSerializer(CamelToSnakeCaseSerializer):
    street = serializers.CharField()
    house_number = serializers.CharField()
    house_letter = serializers.CharField(allow_blank=True)
    zip_code = serializers.CharField()
    suffix = serializers.CharField(allow_blank=True)
    city = serializers.CharField()
    concatenated_address = serializers.CharField()


class WalletSerializer(CamelToSnakeCaseSerializer):
    balance = serializers.FloatField()
    currency = serializers.CharField()


class AccountDetailsResponseSerializer(CamelToSnakeCaseSerializer):
    initials = serializers.CharField(allow_blank=True, required=False)
    last_name = serializers.CharField()
    email = serializers.CharField(allow_blank=True, required=False)
    address = AddressSerializer(required=False)
    phone_number = serializers.CharField(allow_blank=True, required=False)
    client_id = serializers.IntegerField(required=False)
    wallet = WalletSerializer(required=False)
    account_type = serializers.CharField()


class BalanceRequestSerializer(SnakeToCamelCaseSerializer):
    balance = AmountCurrencySerializer()
    redirect = RedirectSerializer()
    locale = serializers.CharField()
