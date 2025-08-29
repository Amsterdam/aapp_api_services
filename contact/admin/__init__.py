from django.contrib import admin
from django.contrib.auth.models import Group, User

from contact.admin.opening_time_admin import (
    CityOfficeOpeningHoursAdmin,
    OpeningHourExceptionsAdmin,
    RegularOpeningHoursAdmin,
)
from contact.admin.survey_entry_admin import SurveyVersionEntryAdmin
from contact.admin.survey_question_admin import QuestionAdmin
from contact.admin.survey_version_admin import (
    SurveyVersionAdmin,
)
from contact.models.contact_models import (
    CityOfficeOpeningHours,
    OpeningHoursException,
    RegularOpeningHours,
)
from contact.models.survey_models import (
    Question,
    SurveyVersion,
    SurveyVersionEntry,
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

admin.site.register(SurveyVersion, SurveyVersionAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(SurveyVersionEntry, SurveyVersionEntryAdmin)
