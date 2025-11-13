from rest_framework import serializers


class ParkingMachineListRequestSerializer(serializers.Serializer):
    permit_zone_id = serializers.CharField(required=False)


class ParkingMachineListResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    payment_area = serializers.CharField()
    start_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    address = serializers.CharField(required=False)
