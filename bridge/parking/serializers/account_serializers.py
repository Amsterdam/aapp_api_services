from rest_framework import serializers


class AccountLoginRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    pin = serializers.CharField()

    def to_representation(self, instance):
        return {
            "reportCode": instance["report_code"],
            "pin": instance["pin"],
        }


class AccountLoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    scope = serializers.CharField()
    id = serializers.CharField(required=False)

    def to_representation(self, instance):
        return {
            "access_token": instance["access_token"],
            "scope": instance["scope"],
            # "id": instance["id"],
        }


class PinCodeRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    phone_number = serializers.CharField()

    def to_representation(self, instance):
        return {
            "reportCode": instance["report_code"],
            "phoneNumber": instance["phone_number"],
        }


class PinCodeResponseSerializer(serializers.Serializer):
    pass
