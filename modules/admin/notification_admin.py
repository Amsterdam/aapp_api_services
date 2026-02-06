from datetime import timedelta

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import ngettext

from modules.services.notification import NotificationService


class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "message",
        "has_url",
        "has_deeplink",
        "send_at",
        "nr_sessions",
        "created_by",
        "created_at",
        "can_change_notification",
    ]
    fields = ["title", "message", "url", "deeplink", "send_at"]
    actions = ["copy_notification"]
    ordering = ["-send_at"]

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and self._notification_is_locked(obj):
            return False
        return True

    @staticmethod
    def _notification_is_locked(notification):
        if (
            notification.send_at is not None
            and notification.send_at < timezone.now() - timedelta(minutes=15)
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

    def response_change(self, request, obj, post_url_continue=None):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        return super().response_change(request, obj, post_url_continue)

    def confirm_send(self, request, object_id):
        obj = self.get_object(request, object_id)
        notification_service = NotificationService()

        if request.method == "POST":
            if "confirm" in request.POST:
                notification_service.send_notification(obj)
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

        # device_ids = notification_service.get_device_ids(obj)
        context = {
            **self.admin_site.each_context(request),
            "notification": obj,
            "notification_deadline": max(
                obj.send_at - timedelta(minutes=15), timezone.now()
            ),
        }
        return TemplateResponse(
            request, "admin/app_notification_confirm_send.html", context
        )

    @admin.display(boolean=True, description="Heeft deeplink")
    def has_deeplink(self, obj) -> bool:
        return obj.deeplink is not None

    @admin.display(boolean=True, description="Heeft url")
    def has_url(self, obj) -> bool:
        return obj.url is not None

    @admin.display(boolean=True, description="Kan gewijzigd worden")
    def can_change_notification(self, obj) -> bool:
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
