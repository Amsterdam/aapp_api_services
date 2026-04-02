from rest_framework import serializers


class StartTransactionRequestSerializer(serializers.Serializer):
    evse_id = serializers.CharField()
    token = serializers.CharField()


class StartTransactionResponseSerializer(serializers.Serializer):
    api_correlation_token = serializers.CharField()


class StopTransactionRequestSerializer(serializers.Serializer):
    api_correlation_token = serializers.CharField()
