from rest_framework import serializers


class SettingsResponseSerializer(serializers.Serializer):
    pre_authorization_amount = serializers.FloatField(allow_null=True)
    session_cleanup_enabled = serializers.BooleanField(allow_null=True)
    session_expiry_hours = serializers.IntegerField(allow_null=True)
    session_expiry_warning_hours = serializers.IntegerField(allow_null=True)
    standard_fine = serializers.IntegerField(allow_null=True)
    vat_fraction = serializers.FloatField(allow_null=True)
