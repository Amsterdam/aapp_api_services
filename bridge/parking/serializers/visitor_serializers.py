from rest_framework import serializers

from bridge.utils import validate_digits


class VisitorTimeBalancePostRequestSerializer(serializers.Serializer):
    seconds_to_transfer = serializers.IntegerField()
    report_code = serializers.CharField()

    def validate_seconds_to_transfer(self, value):
        # check that seconds_to_transfer is a non-zero integer
        if value == 0:
            raise serializers.ValidationError(
                {"seconds_to_transfer": "seconds_to_transfer cannot be zero."}
            )
        return value

    def validate_report_code(self, value):
        # check that report_code contains only digits
        value = validate_digits("report_code", value)
        return value


class VisitorTimeBalanceResponseSerializer(serializers.Serializer):
    main_account = serializers.IntegerField()
    visitor_account = serializers.IntegerField()
