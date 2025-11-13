from django.contrib import admin
from django.contrib.auth.models import Group, User

from survey.admin.survey_admin import SurveyAdmin
from survey.admin.survey_entry_admin import SurveyVersionEntryAdmin
from survey.admin.survey_question_admin import QuestionAdmin
from survey.admin.survey_version_admin import (
    SurveyVersionAdmin,
)
from survey.models import (
    Question,
    Survey,
    SurveyVersion,
    SurveyVersionEntry,
)

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "Vragenlijsten Admin"

admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveyVersion, SurveyVersionAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(SurveyVersionEntry, SurveyVersionEntryAdmin)
