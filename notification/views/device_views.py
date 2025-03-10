from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from core.exceptions import InputDataException
from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from notification.models import (
    Device,
    NotificationPushServiceEnabled,
    NotificationPushTypeEnabled,
)
from notification.serializers.device_serializers import (
    DeviceRegisterRequestSerializer,
    DeviceRegisterResponseSerializer,
)
from notification.serializers.notification_config_serializers import (
    NotificationPushEnabledListSerializer,
    NotificationPushEnabledSerializer,
    NotificationPushServiceEnabledListSerializer,
    NotificationPushServiceEnabledSerializer,
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
        device, created = Device.objects.get_or_create(
            external_id=self.device_id, defaults=serializer.validated_data
        )
        if not created:
            device.firebase_token = serializer.validated_data["firebase_token"]
            device.os = serializer.validated_data["os"]
            device.save()
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


class NotificationPushEnabledView(DeviceIdMixin, generics.GenericAPIView):
    """
    Enable or disable a push for a notification type for a device.
    """

    serializer_class = NotificationPushEnabledSerializer
    http_method_names = ["post", "delete"]

    @extend_schema_for_device_id(
        request=NotificationPushEnabledSerializer,
        success_response=NotificationPushEnabledSerializer,
        exceptions=[ValidationError, NotFound],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = get_object_or_404(Device, external_id=self.device_id)
        config, _ = NotificationPushTypeEnabled.objects.get_or_create(
            device=device,
            notification_type=serializer.validated_data["notification_type"],
        )

        return Response(self.serializer_class(config).data, status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
        additional_params=[NotificationPushEnabledSerializer],
        exceptions=[NotFound],
    )
    def delete(self, request, *args, **kwargs):
        notification_type = request.query_params.get("notification_type")
        if not notification_type:
            raise ValidationError("Notification type is required")

        get_object_or_404(
            NotificationPushTypeEnabled,
            device__external_id=self.device_id,
            notification_type=notification_type,
        ).delete()
        return Response(status=status.HTTP_200_OK)


class NotificationPushEnabledListView(DeviceIdMixin, generics.ListAPIView):
    """
    List all enabled push types for a device.
    """

    serializer_class = NotificationPushEnabledListSerializer

    def get_queryset(self):
        return NotificationPushTypeEnabled.objects.filter(
            device__external_id=self.device_id
        )

    @extend_schema_for_device_id(
        success_response=NotificationPushEnabledListSerializer,
        examples=[
            OpenApiExample(
                name="Example 1",
                value="push-type-1",
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationPushServiceEnabledView(DeviceIdMixin, generics.GenericAPIView):
    """
    Enable or disable a push for a notification type for a device.
    """

    serializer_class = NotificationPushServiceEnabledSerializer
    http_method_names = ["post", "delete"]

    @extend_schema_for_device_id(
        request=NotificationPushServiceEnabledSerializer,
        success_response=NotificationPushServiceEnabledSerializer,
        exceptions=[ValidationError, NotFound],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = get_object_or_404(Device, external_id=self.device_id)
        config, _ = NotificationPushServiceEnabled.objects.get_or_create(
            device=device,
            service_name=serializer.validated_data["service_name"],
        )

        return Response(self.serializer_class(config).data, status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
        additional_params=[NotificationPushServiceEnabledSerializer],
        exceptions=[NotFound],
    )
    def delete(self, request, *args, **kwargs):
        service_name = request.query_params.get("service_name")
        if not service_name:
            raise ValidationError("Service name is required")

        get_object_or_404(
            NotificationPushServiceEnabled,
            device__external_id=self.device_id,
            service_name=service_name,
        ).delete()
        return Response(status=status.HTTP_200_OK)


class NotificationPushServiceEnabledListView(DeviceIdMixin, generics.ListAPIView):
    """
    List all enabled push types for a device.
    """

    serializer_class = NotificationPushServiceEnabledListSerializer

    def get_queryset(self):
        return NotificationPushServiceEnabled.objects.filter(
            device__external_id=self.device_id
        )

    @extend_schema_for_device_id(
        success_response=NotificationPushServiceEnabledListSerializer,
        examples=[
            OpenApiExample(
                name="Example 1",
                value="service-name-1",
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
