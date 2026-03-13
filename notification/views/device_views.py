from drf_spectacular.utils import OpenApiExample
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
import logging
from django.db import IntegrityError
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.response import Response

from core.exceptions import InputDataException
from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from notification.models import (
    Device,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
    WasteNotification
)
from notification.serializers.device_serializers import (
    DeviceRegisterRequestSerializer,
    DeviceRegisterResponseSerializer,
    WasteNotificationSerializer
)
from notification.serializers.notification_config_serializers import (
    NotificationPushModuleDisabledListSerializer,
    NotificationPushModuleDisabledSerializer,
    NotificationPushTypeDisabledListSerializer,
    NotificationPushTypeDisabledSerializer,
)


class DeviceRegisterView(DeviceIdMixin, generics.GenericAPIView):
    """
    API view to register or unregister a device.
    """

    @extend_schema_for_device_id(
        request=DeviceRegisterRequestSerializer,
        success_response=DeviceRegisterResponseSerializer,
        exceptions=[InputDataException],
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new device with firebase token and os if device id is not known yet.
        Update device with firebase token and os if device is already known.
        """
        serializer = DeviceRegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device, _ = Device.objects.update_or_create(
            external_id=self.device_id, defaults=serializer.validated_data
        )
        return Response(
            DeviceRegisterResponseSerializer(device).data, status=status.HTTP_200_OK
        )

    @extend_schema_for_device_id(
        success_response={200: None},
    )
    def delete(self, request, *args, **kwargs):
        """
        Unregister a device by removing its Firebase token.
        """
        try:
            device = Device.objects.get(external_id=self.device_id)
        except Device.DoesNotExist:
            return Response(
                data="Device is not found, but that's okay",
                status=status.HTTP_200_OK,
            )

        # Remove the Firebase token
        device.firebase_token = None
        device.save()

        return Response("Registration removed", status=status.HTTP_200_OK)


class NotificationPushTypeDisabledView(DeviceIdMixin, generics.GenericAPIView):
    """
    Enable or disable a push for a notification type for a device.
    """

    serializer_class = NotificationPushTypeDisabledSerializer
    http_method_names = ["post", "delete"]

    @extend_schema_for_device_id(
        request=NotificationPushTypeDisabledSerializer,
        success_response=NotificationPushTypeDisabledSerializer,
        exceptions=[ValidationError, NotFound],
    )
    def post(self, request, *args, **kwargs):
        """Creating the record disables push for the given type."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = get_or_create_device(self.device_id)
        config, _ = NotificationPushTypeDisabled.objects.get_or_create(
            device=device,
            notification_type=serializer.validated_data["notification_type"],
        )

        return Response(self.serializer_class(config).data, status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
        additional_params=[NotificationPushTypeDisabledSerializer],
        exceptions=[NotFound],
    )
    def delete(self, request, *args, **kwargs):
        """Deleting the record enables push for the given type again."""
        notification_type = request.query_params.get("notification_type")
        if not notification_type:
            raise ValidationError("Notification type is required")

        try:
            NotificationPushTypeDisabled.objects.get(
                device__external_id=self.device_id,
                notification_type=notification_type,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except NotificationPushTypeDisabled.DoesNotExist:
            # Return 204 instead of 404 when not found
            return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationPushTypeDisabledListView(DeviceIdMixin, generics.ListAPIView):
    """
    List all enabled push types for a device.
    """

    serializer_class = NotificationPushTypeDisabledListSerializer

    def get_queryset(self):
        return NotificationPushTypeDisabled.objects.filter(
            device__external_id=self.device_id
        )

    @extend_schema_for_device_id(
        success_response=NotificationPushTypeDisabledListSerializer,
        examples=[
            OpenApiExample(
                name="Example 1",
                value="push-type-1",
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationPushModuleDisabledView(DeviceIdMixin, generics.GenericAPIView):
    """
    Enable or disable a push for a notification type for a device.
    """

    serializer_class = NotificationPushModuleDisabledSerializer
    http_method_names = ["post", "delete"]

    @extend_schema_for_device_id(
        request=NotificationPushModuleDisabledSerializer,
        success_response=NotificationPushModuleDisabledSerializer,
        exceptions=[ValidationError, NotFound],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = get_or_create_device(self.device_id)
        config, _ = NotificationPushModuleDisabled.objects.get_or_create(
            device=device,
            module_slug=serializer.validated_data["module_slug"],
        )

        return Response(self.serializer_class(config).data, status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
        additional_params=[NotificationPushModuleDisabledSerializer],
        exceptions=[NotFound],
    )
    def delete(self, request, *args, **kwargs):
        module_slug = request.query_params.get("module_slug")
        if not module_slug:
            raise ValidationError("Module name is required")

        try:
            NotificationPushModuleDisabled.objects.get(
                device__external_id=self.device_id,
                module_slug=module_slug,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except NotificationPushModuleDisabled.DoesNotExist:
            # Return 204 instead of 404 when not found
            return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationPushModuleDisabledListView(DeviceIdMixin, generics.ListAPIView):
    """
    List all enabled push types for a device.
    """

    serializer_class = NotificationPushModuleDisabledListSerializer

    def get_queryset(self):
        return NotificationPushModuleDisabled.objects.filter(
            device__external_id=self.device_id
        )

    @extend_schema_for_device_id(
        success_response=NotificationPushModuleDisabledListSerializer,
        examples=[
            OpenApiExample(
                name="Example 1",
                value="service-name-1",
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



@extend_schema_for_device_id(success_response=WasteNotificationSerializer)
class WasteNotificationCreateView(DeviceIdMixin, CreateAPIView):
    serializer_class = WasteNotificationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"device_id": self.device_id}
        )
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            get_or_create_device(self.device_id)
        except IntegrityError:
            return Response(
                {"detail": "Notification schedule for this device already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"status": "success"}, status=status.HTTP_201_CREATED, headers=headers
        )


@extend_schema_for_device_id(success_response=WasteNotificationSerializer)
class WasteNotificationDetailView(DeviceIdMixin, RetrieveUpdateDestroyAPIView):
    queryset = WasteNotification.objects.all()
    serializer_class = WasteNotificationSerializer
    lookup_field = "device_id"
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        return self.get_queryset().get(device_id=self.device_id)

    def retrieve(self, request, *args, **kwargs):
        try:
            self.get_object()
        except WasteNotification.DoesNotExist:
            return Response(data={"status": "error", "message": "not found"})
        return Response({"status": "success"})

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except WasteNotification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"status": "success"})

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except WasteNotification.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def get_or_create_device(device_id):
    existing_device = Device.objects.filter(external_id=device_id).first()
    if not existing_device:
        return Device.objects.create(external_id=device_id)
    else:
        return existing_device
