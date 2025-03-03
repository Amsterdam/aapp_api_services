from django.conf import settings

from core.exceptions import MissingDeviceIdHeader


class DeviceIdMixin:
    """
    Mixin to pre-process the request to get the device id
    and bind it to the view.
    This mixin is used specifically for DRF views.
    """

    device_id_required = True

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.device_id = request.headers.get(settings.HEADER_DEVICE_ID)

        if self.device_id == "":
            self.device_id = None

        if self.device_id_required and not self.device_id:
            raise MissingDeviceIdHeader
