from django.contrib import admin
from django.contrib.auth.models import Group, User

from contact.admin.opening_time_admin import (
    CityOfficeOpeningHoursAdmin,
    OpeningHourExceptionsAdmin,
    RegularOpeningHoursAdmin,
)
from contact.models import (
    CityOfficeOpeningHours,
    OpeningHoursException,
    RegularOpeningHours,
)

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "Contact Admin"

admin.site.register(CityOfficeOpeningHours, CityOfficeOpeningHoursAdmin)
admin.site.register(RegularOpeningHours, RegularOpeningHoursAdmin)
admin.site.register(OpeningHoursException, OpeningHourExceptionsAdmin)
admin.site.unregister(RegularOpeningHours)
