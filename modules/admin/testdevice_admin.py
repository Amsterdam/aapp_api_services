from django.contrib import admin


class TestDeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "device_id"]
