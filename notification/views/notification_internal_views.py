import logging
from collections import Counter, defaultdict

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.serializers.error_serializers import get_error_response_serializers
from core.services.scheduled_notification import NotificationServiceError
from notification.crud import NotificationCRUD
from notification.exceptions import PushServiceError
from notification.models import Device, Notification, ScheduledNotification
from notification.serializers.notification_serializers import (
    NotificationCreateResponseSerializer,
    NotificationCreateSerializer,
    ScheduledNotificationDetailSerializer,
    ScheduledNotificationSerializer,
)
from notification.services.push import PushService

logger = logging.getLogger(__name__)


class NotificationAggregateView(generics.CreateAPIView):
    """
    Endpoint to initialize multiple notifications. This endpoint is network isolated and only accessible from other backend services.
    The "make_push" field is ignored in this endpoint, as a single push is made for the entire batch per device id.
    All notifications are required to contain the same module slug.
    """

    serializer_class = NotificationCreateSerializer

    @extend_schema(
        request=NotificationCreateSerializer(many=True),
        responses={
            200: NotificationCreateResponseSerializer(many=True),
            **get_error_response_serializers([PushServiceError, ValidationError]),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        module_slug = self._get_module_slug(validated_data)
        devices_chain, responses = self.create_notifications_without_push(
            validated_data
        )

        created_at = validated_data[0].get("created_at")
        self.push_aggregated_notifications(devices_chain, module_slug, created_at)
        return Response(responses, status=status.HTTP_200_OK)

    def create_notifications_without_push(self, validated_data):
        devices_chain = []
        responses = []
        for notification_data in validated_data:
            device_ids = notification_data.pop("device_ids")
            notification_data.pop("make_push")
            source_notification = Notification(**notification_data)
            notification_crud = NotificationCRUD(
                source_notification, push_enabled=False
            )
            self.create_notifications(
                notification_crud=notification_crud, device_ids=device_ids
            )
            devices_chain += notification_crud.devices_for_push
            responses.append(notification_crud.response_data)
        return devices_chain, responses

    def push_aggregated_notifications(
        self, devices_chain: list[Device], module_slug: str, created_at: str
    ):
        device_id_by_occurrence = self.group_by_occurrence(devices_chain)
        push_service = PushService()
        for occurrence, devices in device_id_by_occurrence.items():
            notifications = [
                Notification(
                    title=module_slug,
                    body=self._get_aggregate_body(occurrence),
                    module_slug=module_slug,
                    context={
                        "type": "AggregateNotification",
                        "module_slug": module_slug,
                    },
                    notification_type=f"{module_slug}:aggregate",
                    created_at=created_at,
                    device=device,
                )
                for device in devices
            ]
            push_service.push(notifications)

    @staticmethod
    def group_by_occurrence(chain) -> dict[int, list[Device]]:
        """
        Returns a dictionary with the number of occurrences as key and a list of devices as value.
        """
        grouped = defaultdict(list)
        for device, count in Counter(chain).items():
            grouped[count].append(device)
        return dict(grouped)

    def _get_module_slug(self, validated_data):
        module_slug = validated_data[0].get("module_slug")
        for notification in validated_data:
            if module_slug != notification.get("module_slug"):
                raise ValidationError(
                    "All notifications must have the same module slug."
                )
        return module_slug

    def _get_aggregate_body(self, occurrence):
        return f"Er staan {occurrence} berichten voor je klaar"

    def create_notifications(
        self, *, notification_crud: NotificationCRUD, device_ids: list[str]
    ):
        try:
            logger.info(
                f"Processing new notification: {notification_crud.source_notification}",
                extra={"device_ids": device_ids},
            )
            devices_qs = self.get_device_queryset(device_ids)
            notification_crud.create(devices_qs)
        except Exception:
            logger.error("Failed to create notifications", exc_info=True)
            raise NotificationServiceError("Failed to create notifications")

    @staticmethod
    def get_device_queryset(device_ids):
        known_devices_qs = Device.objects.filter(external_id__in=device_ids).all()
        known_device_ids = [device.external_id for device in known_devices_qs]
        unknown_device_ids = set(device_ids) - set(known_device_ids)
        if not unknown_device_ids:
            return known_devices_qs

        unknown_devices = [
            Device(external_id=device_id) for device_id in unknown_device_ids
        ]
        Device.objects.bulk_create(unknown_devices, ignore_conflicts=True)
        new_devices_qs = Device.objects.filter(external_id__in=unknown_device_ids)
        logger.warning(f"Created {len(new_devices_qs)} unknown devices.")
        devices_qs = known_devices_qs | new_devices_qs
        return devices_qs


class ScheduledNotificationView(ModelViewSet):
    serializer_class = ScheduledNotificationSerializer
    queryset = ScheduledNotification.objects.all()
    update_fields = [
        "title",
        "body",
        "image",
        "scheduled_for",
        "expires_at",
        "make_push",
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        new_device_ids = validated_data.pop("device_ids")
        devices = create_missing_device_ids(new_device_ids)
        identifier = validated_data["identifier"]
        instance = self.get_queryset().filter(identifier=identifier).first()
        if instance:
            # Perform UPDATE
            old_device_ids = list(instance.devices.all())
            devices = list(set(old_device_ids) | set(devices))  # Add new devices to old

            for attr, value in validated_data.items():
                if attr in self.update_fields:
                    setattr(instance, attr, value)
            with transaction.atomic():
                instance.save()
                instance.devices.set(devices)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Perform CREATE
        with transaction.atomic():
            notification = ScheduledNotification.objects.create(**validated_data)
            notification.devices.set(devices)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ScheduledNotificationDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ScheduledNotification.objects.all()
    serializer_class = ScheduledNotificationDetailSerializer
    lookup_field = "identifier"
    http_method_names = ["get", "patch", "delete"]

    def retrieve(self, request, *args, **kwargs):
        """Return 204 instead of 404 when not found."""
        try:
            instance = ScheduledNotification.objects.get(
                identifier=kwargs["identifier"]
            )
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except ScheduledNotification.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, *args, **kwargs):
        try:
            instance = ScheduledNotification.objects.get(
                identifier=kwargs["identifier"]
            )
            instance.delete()
        except ScheduledNotification.DoesNotExist:
            logger.warning(
                "ScheduledNotification with identifier %s does not exist.",
                kwargs["identifier"],
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


def create_missing_device_ids(device_ids: list[str]) -> list[Device]:
    existing_devices = Device.objects.filter(external_id__in=device_ids).values_list(
        "external_id", flat=True
    )
    missing_device_ids = set(device_ids) - set(existing_devices)
    if missing_device_ids:
        Device.objects.bulk_create(
            Device(external_id=device_id) for device_id in missing_device_ids
        )
    logger.warning(f"Created {len(missing_device_ids)} missing devices.")
    return Device.objects.filter(external_id__in=device_ids)
