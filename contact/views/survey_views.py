from datetime import datetime

from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)

from contact.models.survey_models import Survey, SurveyVersion
from contact.serializers.survey_serializers import (
    SurveySerializer,
    SurveyVersionDetailSerializer,
    SurveyVersionEntrySerializer,
    SurveyVersionSerializer,
)
from core.utils.openapi_utils import extend_schema_for_api_key


class SurveyView(ListAPIView):
    serializer_class = SurveySerializer
    queryset = Survey.objects.all()

    @extend_schema_for_api_key(
        success_response=SurveySerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SurveyVersionView(ListAPIView):
    serializer_class = SurveyVersionSerializer
    queryset = SurveyVersion.objects.all()
    lookup_field = "version"
    lookup_url_kwarg = "version"

    def get_queryset(self):
        unique_code = self.kwargs.get("unique_code")
        survey = get_object_or_404(Survey, unique_code=unique_code)
        return SurveyVersion.objects.filter(survey=survey)

    @extend_schema_for_api_key(
        success_response=SurveyVersionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SurveyVersionDetailView(RetrieveAPIView):
    serializer_class = SurveyVersionDetailSerializer
    lookup_field = "version"
    lookup_url_kwarg = "version"

    def get_queryset(self):
        unique_code = self.kwargs.get("unique_code")
        survey = get_object_or_404(Survey, unique_code=unique_code)
        return SurveyVersion.objects.filter(survey=survey)

    @extend_schema_for_api_key(
        success_response=SurveyVersionDetailSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SurveyVersionLatestView(SurveyVersionDetailView):
    def get_object(self):
        return (
            self.get_queryset()
            .filter(active_from__lt=datetime.now())
            .order_by("version")
            .last()
        )


class SurveyVersionEntryView(CreateAPIView):
    serializer_class = SurveyVersionEntrySerializer

    def get_survey_version(self):
        survey = get_object_or_404(Survey, unique_code=self.kwargs.get("unique_code"))
        survey_version = get_object_or_404(
            SurveyVersion,
            survey=survey,
            version=self.kwargs.get("version"),
        )
        return survey_version

    def perform_create(self, serializer):
        serializer.save(survey_version=self.get_survey_version())

    @extend_schema_for_api_key(
        request=SurveyVersionEntrySerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
