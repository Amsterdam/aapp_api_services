from rest_framework import serializers

from construction_work.models.manage_models import Image


class MetaIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()


class ImagePublicSerializer(serializers.ModelSerializer):
    """Image public serializer"""

    uri = serializers.URLField(source="image")

    class Meta:
        model = Image
        fields = ["uri", "width", "height"]


class DvOImageSourceSerializer(serializers.Serializer):
    uri = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class DvOImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sources = DvOImageSourceSerializer(many=True)
    alternativeText = serializers.CharField()


class DvOProjectSectionLinkSerializer(serializers.Serializer):
    url = serializers.CharField()
    label = serializers.CharField()


class DvOProjectSectionSerializer(serializers.Serializer):
    body = serializers.CharField()
    title = serializers.CharField()
    links = DvOProjectSectionLinkSerializer(many=True)


class DvOProjectSectionsSerializer(serializers.Serializer):
    what = DvOProjectSectionSerializer()
    when = DvOProjectSectionSerializer()
    work = DvOProjectSectionSerializer()
    contact = DvOProjectSectionSerializer()


class DvOCoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class RecursiveField(serializers.Field):
    def to_representation(self, value):
        serializer = DvOProjectTimelineItemSerializer(
            value, many=True, context=self.context
        )
        return serializer.data


class DvOProjectTimelineItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    body = serializers.CharField()
    collapsed = serializers.BooleanField()
    progress = serializers.ChoiceField(choices=["done", "active", "planned"])
    items = serializers.ListField(child=RecursiveField())


class DvOProjectTimelineSerializer(serializers.Serializer):
    title = serializers.CharField()
    intro = serializers.CharField()
    items = DvOProjectTimelineItemSerializer(many=True)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    Special ModelSerializer used for enabling the search function.
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
