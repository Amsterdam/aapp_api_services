from django.contrib import admin
from django.core.checks import messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from waste.services.notification import ManualNotificationService


class NotificationAdmin(admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

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

        device_ids = notification_service.get_device_ids()
        context = {
            **self.admin_site.each_context(request),
            "nr_sessions": len(device_ids),
            "notification": obj,
        }
        return TemplateResponse(
            request, "admin/notification_confirm_send.html", context
        )

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
