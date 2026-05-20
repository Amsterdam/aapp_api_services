from rest_framework import serializers


class DistrictResponseItemSerializer(serializers.Serializer):
    label = serializers.CharField()
    name = serializers.CharField()


class DistrictListResponseSerializer(serializers.Serializer):
    data = DistrictResponseItemSerializer(many=True)
