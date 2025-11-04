from rest_framework import serializers

from core.utils.serializer_utils import (
    CamelToSnakeCaseSerializer,
    SnakeToCamelCaseSerializer,
)


class LicensePlatesGetRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()


class LicensePlatesGetResponseSerializer(CamelToSnakeCaseSerializer):
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField(allow_blank=True, required=False)
    id = serializers.CharField(required=False)

    def to_internal_value(self, data):
        if "vehicleId" in data:
            data = {**data, "id": data["vehicleId"]}
        return super().to_internal_value(data)


class LicensePlatesPostRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField()


class LicensePlatesPostResponseSerializer(CamelToSnakeCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField()
    id = serializers.CharField(required=False)

    def to_internal_value(self, data):
        if "vehicleId" in data:
            data = {**data, "id": data["vehicleId"]}
        return super().to_internal_value(data)


class LicensePlatesDeleteRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
    id = serializers.CharField(required=False, help_text="New in V2")


class LicensePlatesDeleteResponseSerializer(CamelToSnakeCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
    id = serializers.CharField(required=False)

    def to_internal_value(self, data):
        if "vehicleId" in data:
            data = {**data, "id": data["vehicleId"]}
        return super().to_internal_value(data)
