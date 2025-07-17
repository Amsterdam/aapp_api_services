from django.contrib import admin
from django.contrib.auth.models import Group, User

from city_pass.admin.budget_admin import BudgetAdmin
from city_pass.admin.notification_admin import NotificationAdmin
from city_pass.models import Budget, Notification

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "Stadspas notificatie Admin"

admin.site.register(Budget, BudgetAdmin)
admin.site.register(Notification, NotificationAdmin)
