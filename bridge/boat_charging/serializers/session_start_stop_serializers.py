from rest_framework import serializers


class StartTransactionRequestSerializer(serializers.Serializer):
    evse_id = serializers.CharField()


class StartTransactionResponseSerializer(serializers.Serializer):
    transaction_ids = serializers.ListField(child=serializers.CharField())


class StopTransactionRequestSerializer(serializers.Serializer):
    id = serializers.CharField()
