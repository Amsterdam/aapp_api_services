from django.contrib import admin
from django.core.checks import messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from core.authentication import AuthenticationGroupModelAdmin
from core.services.waste_device import WasteDeviceService
from waste.services.notification import ManualNotificationService


class NotificationAdmin(AuthenticationGroupModelAdmin):
    ROUTE_UPDATE_SESSION_KEY = "waste_manual_notification_route_update_state"

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
    ]
    list_select_related = ("created_by",)
    ordering = ["-pk"]
    actions = None
    filter_horizontal = ["affected_routes"]
    change_list_template = "admin/waste/manualnotification/change_list.html"

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "update-routename-data/",
                self.admin_site.admin_view(self.update_routename_data),
                name="notification_update_routename_data",
            ),
            path(
                "<path:object_id>/confirm-send/",
                self.admin_site.admin_view(self.confirm_send),
                name="notification_confirm_send",
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["route_update_url"] = (
            reverse("admin:notification_update_routename_data") + "?restart=1"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def update_routename_data(self, request):
        force_restart = request.GET.get("restart") == "1"
        state = request.session.get(self.ROUTE_UPDATE_SESSION_KEY)

        if force_restart or not state:
            updater = WasteDeviceService()
            total_rows = updater.get_total_rows()
            state = {
                "total": total_rows,
                "processed": 0,
                "updated": 0,
                "skipped": 0,
                "failed": 0,
                "last_pk": "",
                "completed": total_rows == 0,
            }

            if total_rows == 0:
                self.message_user(
                    request,
                    "Geen waste device records gevonden.",
                    level=messages.INFO,
                )

        if not state["completed"]:
            updater = WasteDeviceService()
            batch_result = updater.process_batch(
                batch_size=50,
                last_pk=state["last_pk"],
            )
            state["processed"] += batch_result["processed"]
            state["updated"] += batch_result["updated"]
            state["skipped"] += batch_result["skipped"]
            state["failed"] += batch_result["failed"]
            state["last_pk"] = batch_result["last_pk"]

            if batch_result["processed"] == state["total"]:
                state["completed"] = True
                self.message_user(
                    request,
                    (
                        "Routename update voltooid. "
                        f"{state['updated']} van {state['total']} records bijgewerkt "
                        f"({state['skipped']} overgeslagen, {state['failed']} gefaald)."
                    ),
                    level=messages.INFO,
                )

        request.session[self.ROUTE_UPDATE_SESSION_KEY] = state

        total = state["total"]
        processed = state["processed"]
        progress_percentage = 100 if total == 0 else int((processed / total) * 100)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "total": total,
            "processed": processed,
            "updated": state["updated"],
            "skipped": state["skipped"],
            "failed": state["failed"],
            "completed": state["completed"],
            "progress_percentage": min(progress_percentage, 100),
            "refresh_seconds": 1,
            "changelist_url": reverse("admin:waste_manualnotification_changelist"),
            "restart_url": reverse("admin:notification_update_routename_data")
            + "?restart=1",
        }

        return TemplateResponse(
            request,
            "admin/waste/manualnotification/update_routename_data.html",
            context,
        )

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(
            reverse("admin:notification_confirm_send", args=[obj.pk])
        )

    def confirm_send(self, request, object_id):
        obj = self.get_object(request, object_id)
        notification_service = ManualNotificationService()

        if request.method == "POST":
            if "confirm" in request.POST:
                notification_service.send(obj)
                if obj.nr_sessions:
                    self.message_user(
                        request,
                        f"Bericht verstuurd aan {obj.nr_sessions} gebruikers",
                        level=messages.INFO,
                    )
                else:
                    self.message_user(
                        request,
                        "Geen gebruikers gevonden om bericht aan te versturen!",
                        level=messages.ERROR,
                    )
            else:
                self.message_user(
                    request,
                    "Actie is afgebroken. Bericht is niet verstuurd.",
                    level=messages.WARNING,
                )
                obj.delete()
            return HttpResponseRedirect(
                reverse("admin:waste_manualnotification_changelist")
            )

        device_ids = notification_service.get_device_ids(obj)
        context = {
            **self.admin_site.each_context(request),
            "nr_sessions": len(device_ids),
            "notification": obj,
            "affected_routes": self.affected_routes_display(obj),
        }
        return TemplateResponse(
            request, "admin/notification_confirm_send.html", context
        )

    def affected_routes_display(self, obj):
        affected_routes = list(obj.affected_routes.all())
        if not affected_routes:
            return mark_safe(
                "<div style='color: #999;'>Geen routes geselecteerd.</div>"
            )

        inner = format_html_join(
            "",
            "<div style='padding:2px 0;'>{}</div>",
            ((r.name,) for r in affected_routes),
        )
        return format_html(
            "<div style='border:1px solid #ccc; padding:5px; "
            "max-height:200px; overflow-y:auto; background:#f9f9f9;'>{}</div>",
            inner,
        )

    affected_routes_display.short_description = "Geselecteerde routes"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "send_at",
                "nr_sessions",
                "created_by",
            ]
        return []

    def get_exclude(self, request, obj=None):
        exclude = ["image", "image_set_id", "image_description"]
        if obj:
            return exclude
        else:
            return exclude + ["send_at", "created_by"]

    @admin.display(boolean=True, description="Verstuurd?")
    def send(self, obj) -> bool:
        return obj.send_at is not None and obj.nr_sessions > 0

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_save"] = True
        context["show_save_and_continue"] = False
        context["show_save_and_add_another"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    class Media:
        js = ("js/persist_scroll.js",)
