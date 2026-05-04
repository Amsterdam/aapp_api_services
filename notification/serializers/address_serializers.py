from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer
from core.serializers.mixins import PostalCodeValidationMixin


class AddressRequestSerializer(AddressSerializer, PostalCodeValidationMixin):
    """
    Serializer for validating address data in notification requests.
    Overwrite postcode and bagId field, because they should be provided
    Also overwrite additionLetter and additionNumber field, because they can also be passed empty or as None
    """

    postcode = serializers.CharField(required=True)
    bagId = serializers.CharField(required=True)
    additionLetter = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    additionNumber = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    def validate_postcode(self, value):
        self.validate_postal_code(value)
        return value

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["postal_code"] = validated_data.get("postcode", "")[:4]
        validated_data["bag_nummeraanduiding_id"] = validated_data.get("bagId", "")
        return validated_data
