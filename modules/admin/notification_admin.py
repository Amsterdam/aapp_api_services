from datetime import timedelta

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import ngettext

from modules.models import Notification, TestDevice
from modules.services.notification import NotificationService

DEADLINE_BUFFER_MINUTES = 15


class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "message",
        "has_url",
        "has_deeplink",
        "send_at",
        "nr_sessions",
        "created_by",
        "can_change_notification",
        "real_notification",
    ]
    fields = ["title", "message", "url", "deeplink", "send_at", "is_test"]
    actions = ["copy_notification"]
    ordering = ["-send_at"]

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # delete the scheduled notification in the notification service when the
        # notification is deleted in the admin
        if obj and not self._notification_is_locked(obj):
            notification_service = NotificationService()
            notification_service.delete_scheduled_notification(obj)
            super().delete_model(request, obj)
        else:
            self.message_user(
                request,
                "Bericht is verstuurd en kan niet meer verwijderd worden.",
                level=messages.INFO,
            )

    def has_change_permission(self, request, obj=None):
        if obj and self._notification_is_locked(obj):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and self._notification_is_locked(obj):
            return False
        return True

    @staticmethod
    def _notification_is_locked(notification: Notification) -> bool:
        if (
            notification.send_at is not None
            and notification.send_at
            <= timezone.now() + timedelta(minutes=DEADLINE_BUFFER_MINUTES)
        ):
            return True
        return False

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

    def get_readonly_fields(self, request, obj=None):
        # Make 'is_test' field read-only once the notification is no longer a test,
        # to prevent changing it back to a test notification
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_test is False:
            readonly.append("is_test")
        return readonly

    def response_change(
        self, request, obj: Notification, post_url_continue: str = None
    ):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        return super().response_change(request, obj, post_url_continue)

    def response_add(self, request, obj: Notification, post_url_continue: str = None):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        return super().response_add(request, obj, post_url_continue)

    def confirm_send(self, request, object_id: str):
        obj = self.get_object(request, object_id)
        is_test_notification = obj.is_test
        notification_service = NotificationService()

        if is_test_notification:
            nr_sessions = TestDevice.objects.count()
        else:
            nr_sessions = None

        if request.method == "POST":
            if "confirm" in request.POST:
                notification_service.upsert_scheduled_notification(
                    obj, is_test_notification=is_test_notification
                )
                self.message_user(
                    request,
                    "Bericht aangemaakt voor het versturen.",
                    level=messages.INFO,
                )
            else:
                self.message_user(
                    request,
                    "Actie is afgebroken. Verzenddatum is leeggemaakt.",
                    level=messages.WARNING,
                )
                obj.send_at = None
                obj.save()
            return HttpResponseRedirect(
                reverse("admin:modules_notification_changelist")
            )

        context = {
            **self.admin_site.each_context(request),
            "is_test_notification": is_test_notification,
            "nr_sessions": nr_sessions,
            "notification": obj,
            "notification_deadline": max(
                obj.send_at - timedelta(minutes=DEADLINE_BUFFER_MINUTES), timezone.now()
            ),
        }
        return TemplateResponse(
            request, "admin/app_notification_confirm_send.html", context
        )

    @admin.display(boolean=True, description="Heeft deeplink")
    def has_deeplink(self, obj: Notification) -> bool:
        return obj.deeplink is not None

    @admin.display(boolean=True, description="Heeft url")
    def has_url(self, obj: Notification) -> bool:
        return obj.url is not None

    @admin.display(boolean=True, description="Echte notificatie")
    def real_notification(self, obj: Notification) -> bool:
        return not obj.is_test

    @admin.display(boolean=True, description="Kan gewijzigd worden")
    def can_change_notification(self, obj: Notification) -> bool:
        return not self._notification_is_locked(obj)

    @admin.action(description="Kopieer notificatie zonder verstuurdatum")
    def copy_notification(self, request, queryset):
        for instance in queryset:
            instance.save()
            instance.pk = None
            instance.send_at = None
            instance.save()

        self.message_user(
            request,
            ngettext(
                "%s notification was successfully copied.",
                "%s notifications were successfully copied.",
                len(queryset),
            )
            % len(queryset),
            messages.SUCCESS,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Remove only the bulk delete action
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
