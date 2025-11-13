from rest_framework import serializers


class AccountLoginRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    pin = serializers.CharField()


class AccountLoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    scope = serializers.ChoiceField(choices=["visitor", "permitHolder"])
    access_token_expiration = serializers.DateTimeField()
    version = serializers.ChoiceField(choices=[1, 2])


class AddressSerializer(serializers.Serializer):
    street = serializers.CharField()
    house_number = serializers.CharField()
    house_letter = serializers.CharField(allow_blank=True, required=False)
    zip_code = serializers.CharField()
    suffix = serializers.CharField(allow_blank=True, required=False)
    city = serializers.CharField()
    concatenated_address = serializers.CharField()


class WalletSerializer(serializers.Serializer):
    balance = serializers.FloatField()
    currency = serializers.CharField(required=False, help_text="DEPRECATED")


class AccountDetailsResponseSerializer(serializers.Serializer):
    initials = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    last_name = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    email = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    address = AddressSerializer(required=False, help_text="DEPRECATED")
    phone_number = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    client_id = serializers.IntegerField(required=False, help_text="DEPRECATED")
    wallet = WalletSerializer()
    account_type = serializers.CharField(required=False, help_text="DEPRECATED")
