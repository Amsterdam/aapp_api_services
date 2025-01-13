from rest_framework import serializers


class WastePassNumberRequestSerializer(serializers.Serializer):
    postal_code = serializers.CharField()
    house_number = serializers.CharField(required=False)

    def validate_postal_code(self, value) -> tuple[str, str]:
        """
        Validate the postal code and return the cleaned postal code.
        """
        postal_code = value.replace(" ", "")

        if len(postal_code) != 6:
            raise serializers.ValidationError("Postal code must be 6 characters (4 numbers + 2 letters)")
        
        numbers = postal_code[:4]
        letters = postal_code[4:].upper()

        if not numbers.isdigit():
            raise serializers.ValidationError("First 4 characters must be numbers")

        if not letters.isalpha():
            raise serializers.ValidationError("Last 2 characters must be letters")
            
        return numbers, letters
    
    def validate_house_number(self, value) -> str:
        if value is not None and not value.isdigit():
            raise serializers.ValidationError("House number must be a number")
        return value


class WastePassNumberResponseSerializer(serializers.Serializer):
    district = serializers.CharField()
    pass_number = serializers.CharField()
    has_container = serializers.BooleanField()
