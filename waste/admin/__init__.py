from django.contrib import admin
from django.contrib.auth.models import Group, User

from waste.admin.notification_admin import NotificationAdmin
from waste.admin.recycle_admin import (
    OpeningHoursExceptionAdmin,
    RecycleLocationAdmin,
    RecycleLocationOpeningHoursAdmin,
)
from waste.models import (
    ManualNotification,
    OpeningHoursException,
    RecycleLocation,
    RecycleLocationOpeningHours,
)

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "A&G notificatie en recyclepunt Admin"

admin.site.register(ManualNotification, NotificationAdmin)
admin.site.register(RecycleLocation, RecycleLocationAdmin)
admin.site.register(RecycleLocationOpeningHours, RecycleLocationOpeningHoursAdmin)
admin.site.register(OpeningHoursException, OpeningHoursExceptionAdmin)
