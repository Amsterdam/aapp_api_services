from rest_framework import serializers


class WaitingTimeOutSerializer(serializers.Serializer):
    title = serializers.CharField()
    identifier = serializers.CharField()
    queued = serializers.IntegerField()
    waitingTime = serializers.IntegerField()


class WaitingTimeResultSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    result = WaitingTimeOutSerializer(many=True)
