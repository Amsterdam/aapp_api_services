from rest_framework import serializers


class TermsResponseSerializer(serializers.Serializer):
    content = serializers.CharField()
    version = serializers.IntegerField()
