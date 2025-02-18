from rest_framework import serializers

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
    initials = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    address = AddressSerializer()
    phone_number = serializers.CharField(allow_blank=True)
    client_id = serializers.IntegerField()
    wallet = WalletSerializer()
    account_type = serializers.CharField()
