from django.contrib import admin
from django.contrib.auth.models import Group, User

from waste.admin.notification_admin import NotificationAdmin
from waste.models import ManualNotification

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "A&G notificatie Admin"

admin.site.register(ManualNotification, NotificationAdmin)
