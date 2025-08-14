from django.contrib import admin
from django.core.exceptions import ValidationError

from city_pass.models import Session


class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "title",
        "description",
        "created_at",
        "aantal_gebruiker_sessies",
    ]
    ordering = ["-created_at"]
    actions = None

    def aantal_gebruiker_sessies(self, obj):
        return Session.objects.filter(passdata__budgets=obj).distinct().count()

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        raise ValidationError("Deletion of Budget is not allowed.")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["created_at"]
        return []

    class Media:
        js = ("js/persist_scroll.js",)
