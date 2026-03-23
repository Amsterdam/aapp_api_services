from rest_framework import serializers

from core.serializers.mixins import PostalCodeValidationMixin


class AddressRequestSerializer(serializers.Serializer, PostalCodeValidationMixin):
    bag_nummeraanduiding_id = serializers.CharField()
    postal_code = serializers.CharField()
