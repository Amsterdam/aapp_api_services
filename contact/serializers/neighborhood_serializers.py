from rest_framework import serializers

from contact.models import NeighborhoodNotes, NeighborhoodNotesImage
from core.services.image_set import ImageSetService


class ImageCreateRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    description = serializers.CharField(required=False)


class ImageCreateResponseSerializer(serializers.Serializer):
    image_set_id = serializers.IntegerField()


class CreateNeighborhoodNoteRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeighborhoodNotes
        fields = (
            "title",
            "body",
            "contact_name",
            "contact_number",
            "lat",
            "lng",
            "image_set_id",
        )

    image_set_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        external_device_id = self.context.get("external_device_id")
        if not external_device_id:
            request = self.context.get("request")
            if request:
                external_device_id = request.headers.get(
                    "external_device_id"
                ) or request.headers.get("External-Device-Id")

        if not external_device_id:
            raise serializers.ValidationError(
                {"external_device_id": "Missing required device id header."}
            )

        attrs["external_device_id"] = external_device_id
        return attrs

    def create(self, validated_data):
        image_set_id = validated_data.pop("image_set_id", None)
        new_note = NeighborhoodNotes.objects.create(**validated_data)

        if image_set_id:
            self.construct_neighborhood_note_image(image_set_id, note=new_note)

        return new_note

    @staticmethod
    def construct_neighborhood_note_image(image_set_id, note=None):
        image_set_data = ImageSetService().get(image_set_id)
        # Upsert note images from image-set variants.
        image_sources = [
            NeighborhoodNotesImage(
                note=note,
                foreign_id=image_set_data[
                    "id"
                ],  # use the image set id as the image foreign_id for reference.
                uri=v["image"],
                width=v["width"],
                height=v["height"],
            )
            for v in image_set_data["variants"]
        ]
        # Upsert new images (create or update width/height)
        NeighborhoodNotesImage.objects.bulk_create(
            image_sources,
            update_conflicts=True,
            unique_fields=["note", "uri"],
            update_fields=["width", "height"],
        )


class CreateNeighborhoodNoteResponseSerializer(serializers.Serializer):
    note_id = serializers.IntegerField()


class RetrieveNeighborhoodNotesResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeighborhoodNotes
        exclude = ["external_device_id"]


class RetrieveNeighborhoodNotesRequestSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)
