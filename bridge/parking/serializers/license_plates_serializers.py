from rest_framework import serializers

from bridge.utils import validate_digits


class LicensePlatesGetRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField(required=True)

    def validate_report_code(self, value):
        # check that report_code only consists of numbers
        value = validate_digits("report_code", value)
        return value


class LicensePlatesGetResponseSerializer(serializers.Serializer):
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField(
        allow_blank=True, required=False, help_text="Empty for permit plates"
    )
    id = serializers.IntegerField(help_text="New in V2")
    created_at = serializers.DateTimeField(
        required=False, help_text="New in V2, only for favorite plates"
    )
    activated_at = serializers.DateTimeField(
        required=False, help_text="New in V2, only for permit plates"
    )
    is_future = serializers.BooleanField(
        required=False, help_text="New in V2, only for permit plates"
    )

    def validate(self, data):
        # Check one of created_at and activated_at is set, but not both
        if "created_at" not in data and "activated_at" not in data:
            raise serializers.ValidationError(
                "One of created_at or activated_at must be set."
            )

        # chech that if activated_at is set, is_future is also set
        if "activated_at" in data and "is_future" not in data:
            raise serializers.ValidationError(
                "If activated_at is set, is_future must also be set."
            )
        return data


class LicensePlatesPostRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    vehicle_id = serializers.CharField(max_length=25)
    visitor_name = serializers.CharField(max_length=50)


class LicensePlatesPostResponseSerializer(serializers.Serializer):
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField()
    id = serializers.CharField(help_text="New in V2")


class LicensePlatesDeleteRequestSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="New in V2")
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    vehicle_id = serializers.CharField(required=False, help_text="DEPRECATED")


class LicensePlatesDeleteResponseSerializer(serializers.Serializer):
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    vehicle_id = serializers.CharField(required=False, help_text="DEPRECATED")
