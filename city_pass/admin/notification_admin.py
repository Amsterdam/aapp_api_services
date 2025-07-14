from client_side_image_cropping import DcsicAdminMixin
from client_side_image_cropping.widgets import ClientsideCroppingWidget
from django import forms
from django.contrib import admin
from django.core.checks import messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from city_pass.models import Notification
from city_pass.services.notification import NotificationService
from core.services.image_set import ImageSetService


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = "__all__"
        widgets = {
            "image": ClientsideCroppingWidget(
                width=1280,
                height=720,
                preview_width=320,
                preview_height=180,
            ),
        }


class NotificationAdmin(DcsicAdminMixin, admin.ModelAdmin):
    list_display = [
        "title",
        "message",
        "send",
        "nr_sessions",
        "selected_budgets",
        "created_by",
        "send_at",
    ]
    list_select_related = ("created_by",)
    ordering = ["-pk"]
    actions = None
    filter_horizontal = ("budgets",)
    form = NotificationForm

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        if obj.image:
            image = ImageSetService().upload(
                image=obj.image, description=obj.image_description
            )
            obj.image_set_id = image["id"]
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
        notification_service = NotificationService()
        notification_service.set_device_ids(obj)

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
                reverse("admin:city_pass_notification_changelist")
            )

        context = {
            **self.admin_site.each_context(request),
            "nr_sessions": len(notification_service.device_ids),
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
                "image_preview",
                "send_at",
                "nr_sessions",
                "created_by",
                "budgets_display",
            ]
        return []

    def get_exclude(self, request, obj=None):
        exclude = ["image_set_id"]
        if obj:
            return exclude + ["budgets"]
        return exclude + ["send_at", "created_by"]

    @admin.display(boolean=True, description="Verstuurd?")
    def send(self, obj) -> bool:
        return obj.send_at is not None and obj.nr_sessions > 0

    def budgets_display(self, obj):
        budgets = list(obj.budgets.all())
        if not budgets:
            return format_html(
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

    def image_preview(self, obj):
        if not obj.image:
            return "(No image)"
        return format_html(
            '<div style="border:1px solid #ccc; '
            "padding:5px; display:inline-block; "
            'background:#f9f9f9;">'
            '<img src="{}" style="max-width:200px; '
            'max-height:200px;" /></div>',
            obj.image.url,
        )

    image_preview.short_description = "Afbeelding Preview"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_save"] = True
        context["show_save_and_continue"] = False
        context["show_save_and_add_another"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    class Media:
        js = ("js/persist_scroll.js",)
