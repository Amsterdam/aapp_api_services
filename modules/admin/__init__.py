from django.contrib import admin
from django.contrib.auth.models import Group, User

from modules.admin.app_release_admin import AppReleaseAdmin
from modules.admin.module_admin import ModuleAdmin
from modules.admin.notification_admin import NotificationAdmin
from modules.admin.testdevice_admin import TestDeviceAdmin
from modules.models import AppRelease, Module, Notification, TestDevice

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "Modules Admin"

admin.site.register(Module, ModuleAdmin)
admin.site.register(AppRelease, AppReleaseAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(TestDevice, TestDeviceAdmin)
