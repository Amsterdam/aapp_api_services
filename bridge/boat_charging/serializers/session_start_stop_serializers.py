from rest_framework import serializers


class SessionInitRequestSerializer(serializers.Serializer):
    station_id = serializers.CharField()
    socket_number = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    return_url = serializers.URLField()


class SessionInitResponseSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()
