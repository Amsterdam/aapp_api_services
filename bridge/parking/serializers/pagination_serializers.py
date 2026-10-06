from rest_framework import serializers


class PaginationPageSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    size = serializers.IntegerField()
    totalElements = serializers.IntegerField(allow_null=True)
    totalPages = serializers.IntegerField(allow_null=True)


class PaginationLinkHrefSerializer(serializers.Serializer):
    href = serializers.URLField()


class PaginationLinksSerializer(serializers.Serializer):
    self = PaginationLinkHrefSerializer()
    next = PaginationLinkHrefSerializer(required=False)
    previous = PaginationLinkHrefSerializer(required=False)
