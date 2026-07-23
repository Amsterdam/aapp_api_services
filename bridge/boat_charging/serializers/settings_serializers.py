from rest_framework import serializers


class SettingsResponseSerializer(serializers.Serializer):
    pre_authorization_amount = serializers.FloatField()
    session_cleanup_enabled = serializers.BooleanField()
    session_expiry_hours = serializers.IntegerField()
    session_expiry_warning_hours = serializers.IntegerField()
    standard_fine = serializers.IntegerField()
