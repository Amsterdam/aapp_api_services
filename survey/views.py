from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.pagination import PageNumberPagination

from core.utils.openapi_utils import extend_schema_for_api_key
from survey.models import Survey, SurveyConfiguration, SurveyVersion, SurveyVersionEntry
from survey.serializers.survey_serializers import (
    SurveyConfigResponseSerializer,
    SurveySerializer,
    SurveyVersionDetailSerializer,
    SurveyVersionEntryListSerializer,
    SurveyVersionEntrySerializer,
    SurveyVersionSerializer,
)


class SurveyView(ListAPIView):
    serializer_class = SurveySerializer
    queryset = Survey.objects.all()

    @extend_schema_for_api_key(
        success_response=SurveySerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SurveyConfigView(RetrieveAPIView):
    serializer_class = SurveyConfigResponseSerializer
    lookup_field = "location"
    lookup_url_kwarg = "location"
    queryset = SurveyConfiguration.objects.all().prefetch_related(
        "survey__surveyversion_set"
    )

    @extend_schema_for_api_key(
        success_response=SurveyConfigResponseSerializer,
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


class SurveyVersionEntryListView(ListAPIView):
    class DefaultPagination(PageNumberPagination):
        page_size = 25
        page_size_query_param = "page_size"
        max_page_size = 100

    serializer_class = SurveyVersionEntryListSerializer
    queryset = (
        SurveyVersionEntry.objects.all()
        .prefetch_related("answers")
        .prefetch_related("survey_version__survey")
    )
    pagination_class = DefaultPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        survey_version = self.request.query_params.get("survey_version")
        survey_unique_code = self.request.query_params.get("survey_unique_code")
        if survey_version:
            queryset = queryset.filter(survey_version__version=survey_version)
        if survey_unique_code:
            queryset = queryset.filter(
                survey_version__survey__unique_code=survey_unique_code
            )
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="survey_version",
                type=OpenApiTypes.INT,
                required=False,
                description="Filter by SurveyVersion id.",
            ),
            OpenApiParameter(
                name="survey_unique_code",
                type=OpenApiTypes.STR,
                required=False,
                description="Filter by Survey unique_code.",
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
