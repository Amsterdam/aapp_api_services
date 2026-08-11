from datetime import timedelta

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from core.authentication import AuthenticationGroupModelAdmin
from waste.models import ManualNotification
from waste.services.notification import ManualNotificationService

DEADLINE_BUFFER_MINUTES = 15


class NotificationAdmin(AuthenticationGroupModelAdmin):
    authentication_groups = (
        "waste-publisher",
        "waste-delegated",
        "waste-notification-publisher",
        "waste-notification-delegated",
    )
    list_display = [
        "title",
        "message",
        "send",
        "nr_sessions",
        "created_by",
        "send_at",
        "can_change_notification",
    ]
    list_select_related = ("created_by",)
    ordering = ["-send_at"]
    actions = None

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if obj and not self._notification_is_locked(obj):
            notification_service = ManualNotificationService()
            notification_service.delete_notification(obj)
            super().delete_model(request, obj)
        else:
            self.message_user(
                request,
                f"Bericht kan niet verwijderd worden, omdat deze al verstuurd is of binnen de bufferperiode (van {DEADLINE_BUFFER_MINUTES} minuten) valt.",
                level=messages.INFO,
            )

    def has_change_permission(self, request, obj=None):
        if obj and self._notification_is_locked(obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and self._notification_is_locked(obj):
            return False
        return super().has_delete_permission(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/confirm-send/",
                self.admin_site.admin_view(self.confirm_send),
                name="notification_confirm_send",
            ),
        ]
        return custom + urls

    def response_add(self, request, obj: ManualNotification, post_url_continue=None):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj: ManualNotification):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        # if notification has no send date, we make sure the scheduled notification is deleted
        # if it was created before with a send date and the user changed it to no send date
        else:
            notification_service = ManualNotificationService()
            notification_service.delete_notification(obj)
            obj.send_at = None
            obj.nr_sessions = 0
            obj.save(update_fields=["send_at", "nr_sessions"])
        return super().response_change(request, obj)

    def confirm_send(self, request, object_id):
        obj = self.get_object(request, object_id)
        notification_service = ManualNotificationService()

        if request.method == "POST":
            if "confirm" in request.POST:
                notification_service.send(obj)
                if obj.nr_sessions:
                    self.message_user(
                        request,
                        f"Bericht aangemaakt voor {obj.nr_sessions} gebruikers",
                        level=messages.INFO,
                    )
                else:
                    self.message_user(
                        request,
                        "Geen gebruikers gevonden om bericht voor aan te maken!",
                        level=messages.ERROR,
                    )
            else:
                self.message_user(
                    request,
                    "Actie is afgebroken. Verzenddatum is leeggemaakt.",
                    level=messages.WARNING,
                )
                notification_service.delete_notification(obj)
                obj.send_at = None
                obj.nr_sessions = 0
                obj.save(update_fields=["send_at", "nr_sessions"])
            return HttpResponseRedirect(
                reverse("admin:waste_manualnotification_changelist")
            )

        device_ids = notification_service.get_device_ids()
        context = {
            **self.admin_site.each_context(request),
            "nr_sessions": len(device_ids),
            "notification": obj,
            "notification_deadline": max(
                obj.send_at - timedelta(minutes=DEADLINE_BUFFER_MINUTES),
                timezone.now(),
            ),
        }
        return TemplateResponse(
            request, "admin/notification_confirm_send.html", context
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "nr_sessions",
                "created_by",
            ]
        return []

    def get_exclude(self, request, obj=None):
        exclude = ["image", "image_set_id", "image_description"]
        if obj:
            return exclude
        else:
            return exclude + ["created_by"]

    @admin.display(boolean=True, description="Verstuurd?")
    def send(self, obj: ManualNotification) -> bool:
        return (
            obj.send_at is not None
            and obj.nr_sessions > 0
            and obj.send_at <= timezone.now()
        )

    @admin.display(boolean=True, description="Kan gewijzigd worden")
    def can_change_notification(self, obj: ManualNotification) -> bool:
        return not self._notification_is_locked(obj)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_save"] = True
        context["show_save_and_continue"] = False
        context["show_save_and_add_another"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    @staticmethod
    def _notification_is_locked(notification: ManualNotification) -> bool:
        if (
            notification.send_at is not None
            and notification.send_at
            <= timezone.now() + timedelta(minutes=DEADLINE_BUFFER_MINUTES)
        ):
            return True
        return False

    class Media:
        js = ("js/persist_scroll.js",)
