from rest_framework import serializers

from core.serializers.mixins import PostalCodeValidationMixin


class AddressRequestSerializer(serializers.Serializer, PostalCodeValidationMixin):
    bag_nummeraanduiding_id = serializers.CharField()
    postal_code = serializers.CharField(max_length=4, min_length=4)
