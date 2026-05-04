from rest_framework import generics, status
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from notification.models import BurningGuideDevice, WasteDevice
from notification.serializers.address_serializers import (
    AddressRequestSerializer,
)


@extend_schema_for_device_id()
class AddressView(DeviceIdMixin, generics.GenericAPIView):
    """Create/update and delete the address information for the waste and burning guide device records"""

    serializer_class = AddressRequestSerializer

    http_method_names = ["post", "delete"]

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        waste_device = self._get_waste_device_instance()
        if waste_device:
            # if there is a waste device, update the existing waste address
            waste_device.bag_nummeraanduiding_id = serializer.validated_data[
                "bag_nummeraanduiding_id"
            ]
            waste_device.save()

        burning_guide_device = self._get_burning_guide_device_instance()
        if burning_guide_device:
            # if there is a burning guide device, update the existing burning guide address
            burning_guide_device.postal_code = serializer.validated_data["postal_code"]
            burning_guide_device.save()

        return Response(status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):

        # for both the waste and burning guide device,
        # delete the address by setting the bag_nummeraanduiding_id and postal_code to None respectively
        waste_device = self._get_waste_device_instance()
        if waste_device:
            waste_device.bag_nummeraanduiding_id = None
            waste_device.save()

        burning_guide_device = self._get_burning_guide_device_instance()
        if burning_guide_device:
            burning_guide_device.postal_code = None
            burning_guide_device.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_waste_device_instance(self):
        return WasteDevice.objects.filter(device_id=self.device_id).first()

    def _get_burning_guide_device_instance(self):
        return BurningGuideDevice.objects.filter(device_id=self.device_id).first()
