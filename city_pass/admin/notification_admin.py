from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from city_pass.models import Notification
from city_pass.services.notification import NotificationService


class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "message",
        "send",
        "nr_sessions",
        "selected_budgets",
        "created_by",
        "send_at",
        "can_change_notification",
    ]
    list_select_related = ("created_by",)
    ordering = ["-pk"]
    actions = None
    filter_horizontal = ("budgets",)

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # delete the scheduled notification in the notification service when the
        # notification is deleted in the admin
        if obj and not self._notification_is_locked(obj):
            notification_service = NotificationService()
            notification_service.delete_notification(obj)
            super().delete_model(request, obj)
        else:
            self.message_user(
                request,
                "Bericht kan niet verwijderd worden, omdat deze al verstuurd is.",
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

    def response_change(self, request, obj: Notification):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        # if notification has no send date, we make sure the scheduled notification is deleted
        # if it was created before with a send date and the user changed it to no send date
        else:
            notification_service = NotificationService()
            notification_service.delete_notification(obj)
            obj.send_at = None
            obj.nr_sessions = 0
            obj.save(update_fields=["send_at", "nr_sessions"])
        return super().response_change(request, obj)

    def response_add(self, request, obj: Notification, post_url_continue: str = None):
        # only ask for confirmation if notification has send date
        if obj.send_at is not None:
            return HttpResponseRedirect(
                reverse("admin:notification_confirm_send", args=[obj.pk])
            )
        return super().response_add(request, obj, post_url_continue)

    def confirm_send(self, request, object_id):
        obj = self.get_object(request, object_id)
        notification_service = NotificationService()

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
                # make sure the scheduled notification is deleted if it was created before the user canceled the action
                notification_service.delete_notification(obj)
                obj.send_at = None
                obj.nr_sessions = 0
                obj.save(update_fields=["send_at", "nr_sessions"])
            return HttpResponseRedirect(
                reverse("admin:city_pass_notification_changelist")
            )

        device_ids = notification_service.get_device_qs(obj)
        context = {
            **self.admin_site.each_context(request),
            "nr_sessions": device_ids.count(),
            "notification": obj,
            "budgets": self.budgets_display(obj),
        }
        return TemplateResponse(
            request, "admin/notification_confirm_send.html", context
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "nr_sessions",
                "created_by",
                "budgets_display",
            ]
        return []

    def get_exclude(self, request, obj=None):
        exclude = ["image", "image_set_id", "image_description"]
        if obj:
            return exclude + ["budgets"]
        else:
            return exclude + ["created_by"]

    @admin.display(boolean=True, description="Verstuurd?")
    def send(self, obj) -> bool:
        return (
            obj.send_at is not None
            and obj.nr_sessions > 0
            and obj.send_at <= timezone.now()
        )

    def budgets_display(self, obj):
        budgets = list(obj.budgets.all())
        if not budgets:
            return mark_safe(
                "<div style='color: #999;'>Geen budget filter toegepast.</div>"
            )

        inner = format_html_join(
            "",
            "<div style='padding:2px 0;'><a href='{}'>{}</a></div>",
            (
                (
                    reverse("admin:city_pass_budget_change", args=(b.pk,)),
                    b.title,
                )
                for b in obj.budgets.all()
            ),
        )
        return format_html(
            "<div style='border:1px solid #ccc; padding:5px; "
            "max-height:200px; overflow-y:auto; background:#f9f9f9;'>{}</div>",
            inner,
        )

    budgets_display.short_description = "Geselecteerde budgetten"

    def selected_budgets(self, obj):
        count = obj.budgets.count()
        if count == 0:
            return "Verstuurd naar alle gebruikers"
        return count

    selected_budgets.short_description = "Geselecteerde budgetten"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_save"] = True
        context["show_save_and_continue"] = False
        context["show_save_and_add_another"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    @admin.display(boolean=True, description="Kan gewijzigd worden")
    def can_change_notification(self, obj: Notification) -> bool:
        return not self._notification_is_locked(obj)

    @staticmethod
    def _notification_is_locked(notification: Notification) -> bool:
        if notification.send_at is not None and notification.send_at <= timezone.now():
            return True
        return False

    class Media:
        js = ("js/persist_scroll.js",)
