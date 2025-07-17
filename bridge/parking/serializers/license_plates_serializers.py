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


class LicensePlatesPostRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField()


class LicensePlatesPostResponseSerializer(CamelToSnakeCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
    visitor_name = serializers.CharField()


class LicensePlatesDeleteRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()


class LicensePlatesDeleteResponseSerializer(CamelToSnakeCaseSerializer):
    report_code = serializers.CharField()
    vehicle_id = serializers.CharField()
