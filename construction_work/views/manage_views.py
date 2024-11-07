import logging

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from construction_work.authentication import EntraIDAuthentication
from construction_work.exceptions import MissingProjectIdBody
from construction_work.models import (
    Project,
    ProjectManager,
    WarningImage,
    WarningMessage,
)
from construction_work.permissions import (
    IsEditor,
    IsPublisher,
    IsPublisherOnlyReadOwnData,
    IsPublisherOnlyUpdateOwnWarning,
)
from construction_work.serializers.image_serializer import ImageCreateSerializer
from construction_work.serializers.project_serializers import (
    ProjectDetailsForManagementSerializer,
    ProjectListForManageSerializer,
    ProjectManagerCreateResultSerializer,
    ProjectManagerNameEmailSerializer,
    ProjectManagerWithProjectsSerializer,
    WarningMessageCreateUpdateSerializer,
    WarningMessageForManagementSerializer,
    WarningMessageWithNotificationResultSerializer,
)
from construction_work.services.push_notifications import trigger_push_notification
from construction_work.utils.auth_utils import (
    get_manager_type,
    get_project_manager_from_token,
)
from construction_work.utils.openapi_utils import AutoExtendSchemaMixin
from construction_work.utils.openapi_utils import (
    extend_schema_for_entra as extend_schema,
)
from construction_work.utils.query_utils import get_warningimage_width_height_prefetch
from construction_work.utils.url_utils import get_media_url

logger = logging.getLogger(__name__)


class PublisherListCreateView(AutoExtendSchemaMixin, generics.ListCreateAPIView):
    """
    API view to list all project managers or create a new one.
    """

    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsEditor]
    queryset = ProjectManager.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            # Use this serializer for input validation during creation
            return ProjectManagerNameEmailSerializer
        else:
            # Use this serializer for listing project managers
            return ProjectManagerWithProjectsSerializer

    @extend_schema(success_response=ProjectManagerCreateResultSerializer)
    def post(self, request, *args, **kwargs):
        """
        Create a new project manager.
        """
        # Use the serializer defined in get_serializer_class()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project_manager = serializer.save()

        # Serialize the created project manager with a different serializer
        result_serializer = ProjectManagerCreateResultSerializer(project_manager)
        return Response(result_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(success_response=ProjectManagerWithProjectsSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublisherDetailView(AutoExtendSchemaMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a ProjectManager (Publisher).
    """

    queryset = ProjectManager.objects.all()
    serializer_class = ProjectManagerWithProjectsSerializer
    authentication_classes = [EntraIDAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsPublisherOnlyReadOwnData]
        elif self.request.method in ["PATCH", "DELETE"]:
            permission_classes = [IsEditor]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_object(self):
        obj = super().get_object()
        # Additional permission checks for GET requests
        if self.request.method == "GET":
            manager_type = get_manager_type(self.request.auth)
            if manager_type.is_publisher() and not manager_type.is_editor():
                # Publishers can only access their own data
                self_publisher = get_project_manager_from_token(self.request.auth)
                if not self_publisher:
                    raise PermissionDenied("Publisher in token not known")
                if obj != self_publisher:
                    raise PermissionDenied("Publisher can only access self")
        return obj

    @extend_schema(
        success_response=str,
        examples=[OpenApiExample("Example 1", value="Object removed")],
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data="Object removed", status=status.HTTP_200_OK)


class PublisherAssignProjectView(AutoExtendSchemaMixin, generics.GenericAPIView):
    """
    Assign a project to a publisher.
    """

    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsEditor]

    @extend_schema(
        success_response=str,
        examples=[OpenApiExample("Example 1", value="Publisher assigned to project")],
    )
    def post(self, request, pk, *args, **kwargs):
        publisher = get_object_or_404(ProjectManager, pk=pk)
        project_id = request.data.get("project_id")
        if not project_id:
            raise MissingProjectIdBody

        project = get_object_or_404(Project, pk=project_id)
        publisher.projects.add(project)
        return Response(data="Publisher assigned to project", status=status.HTTP_200_OK)


class PublisherUnassignProjectView(AutoExtendSchemaMixin, generics.GenericAPIView):
    """
    Unassign a project from a publisher.
    """

    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsEditor]

    @extend_schema(
        success_response=str,
        examples=[
            OpenApiExample("Example 1", value="Publisher unassigned from project")
        ],
    )
    def delete(self, request, pk, project_id, *args, **kwargs):
        publisher = get_object_or_404(ProjectManager, pk=pk)
        project = get_object_or_404(Project, pk=project_id)
        publisher.projects.remove(project)
        return Response(
            data="Publisher unassigned from project", status=status.HTTP_200_OK
        )


class ProjectListForManageView(AutoExtendSchemaMixin, generics.ListAPIView):
    """
    Return list of all projects, limit to own projects if request is from publisher.
    """

    serializer_class = ProjectListForManageSerializer
    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsPublisherOnlyUpdateOwnWarning]

    def get_queryset(self):
        token_data = self.request.auth
        manager_type = get_manager_type(token_data)

        if manager_type.is_editor():
            projects = Project.objects.all()
        elif manager_type.is_publisher():
            publisher = get_project_manager_from_token(token_data)
            if not publisher:
                raise PermissionDenied("Publisher not known")
            projects = publisher.projects.all()
        else:
            projects = Project.objects.none()

        projects = projects.prefetch_related(
            Prefetch(
                "projectmanager_set",
                queryset=ProjectManager.objects.only("name", "email"),
            ),
            Prefetch(
                "warningmessage_set",
                queryset=WarningMessage.objects.prefetch_related(
                    get_warningimage_width_height_prefetch()
                ),
            ),
            Prefetch("article_set"),
        )

        return projects


class ProjectDetailsForManageView(AutoExtendSchemaMixin, generics.RetrieveAPIView):
    """
    Retrieve project details for management.
    """

    serializer_class = ProjectDetailsForManagementSerializer
    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsPublisherOnlyUpdateOwnWarning]

    def get_queryset(self):
        return Project.objects.filter(active=True)

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "media_url": get_media_url(self.request),
            }
        )
        return context


class WarningMessageCreateView(AutoExtendSchemaMixin, generics.CreateAPIView):
    """
    Create a new warning message for a project.
    """

    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsPublisher]
    serializer_class = WarningMessageWithNotificationResultSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        token_data = request.auth
        manager_type = get_manager_type(token_data)

        # Determine project_manager
        if manager_type.is_editor():
            project_manager = ProjectManager.objects.filter(
                email=token_data.get("upn")
            ).first()
            if not project_manager:
                name_in_token = (
                    f"{token_data.get('given_name')} {token_data.get('family_name')}"
                )
                project_manager = ProjectManager.objects.create(
                    name=name_in_token,
                    email=token_data.get("upn"),
                )
        else:
            project_manager = get_project_manager_from_token(token_data)
            if not project_manager:
                logger.warning("Publisher not known")
                raise PermissionDenied("Publisher not known")

        # Get project by id
        project_id = self.kwargs.get("pk")
        project = get_object_or_404(Project, pk=project_id)

        # Check if project_manager is related to project
        if project not in project_manager.projects.all():
            if manager_type.is_editor():
                project_manager.projects.add(project)
            else:
                logger.warning("Publisher not related to project")
                raise PermissionDenied("Publisher not related to project")

        # Validate warning message data
        create_message_serializer = WarningMessageCreateUpdateSerializer(
            data=request.data,
            context={
                "project": project,
                "project_manager": project_manager,
            },
        )
        create_message_serializer.is_valid(raise_exception=True)
        new_warning = create_message_serializer.save()

        # Handle image data if provided
        image_data = request.data.get("image")
        if image_data:
            image_serializer = ImageCreateSerializer(data=image_data)
            image_serializer.is_valid(raise_exception=True)

            # Create WarningImage and associate images
            new_image_ids = image_serializer.save()
            warning_image = WarningImage.objects.create(
                warning=new_warning,
            )
            warning_image.images.set(new_image_ids)

        # Handle push notification
        send_push_notification = create_message_serializer.validated_data.get(
            "send_push_notification"
        )
        push_ok = False
        push_message = None
        if send_push_notification:
            push_ok, push_message = trigger_push_notification(new_warning)

        # Return the created warning with notification result
        return_serializer = WarningMessageWithNotificationResultSerializer(
            instance=new_warning,
            context={
                "push_ok": push_ok,
                "push_message": push_message,
                "media_url": get_media_url(request),
            },
        )
        return Response(return_serializer.data, status=status.HTTP_200_OK)


class WarningMessageDetailView(
    AutoExtendSchemaMixin, generics.RetrieveUpdateDestroyAPIView
):
    authentication_classes = [EntraIDAuthentication]
    serializer_class = WarningMessageForManagementSerializer

    def get_queryset(self):
        # Prefetch related data
        return WarningMessage.objects.prefetch_related(
            get_warningimage_width_height_prefetch()
        )

    def get_object(self):
        obj = super().get_object()

        # Validate manager-project relationship
        token_data = self.request.auth
        manager_type = get_manager_type(token_data)

        if manager_type.is_publisher():
            manager = get_project_manager_from_token(token_data)
            if not manager:
                raise PermissionDenied("Publisher not known")
            if obj.project not in manager.projects.all():
                raise PermissionDenied("Publisher cannot access this warning")

        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "media_url": get_media_url(self.request),
            }
        )
        return context

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsPublisher]
        elif self.request.method in ["PATCH", "DELETE"]:
            permission_classes = [IsPublisherOnlyUpdateOwnWarning]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    @extend_schema(success_response=WarningMessageWithNotificationResultSerializer)
    def partial_update(self, request, *args, **kwargs):
        warning = self.get_object()

        # Update the warning message
        serializer = WarningMessageCreateUpdateSerializer(
            instance=warning,
            data=request.data,
            context={
                "project": warning.project,
                "project_manager": warning.project_manager,
            },
            partial=True,  # Allow partial updates
        )
        serializer.is_valid(raise_exception=True)
        warning = serializer.save()

        # Handle image data if provided
        image_data = request.data.get("image")
        if image_data:
            image_serializer = ImageCreateSerializer(data=image_data)
            image_serializer.is_valid(raise_exception=True)

            # Delete existing images
            warning.warningimage_set.all().delete()

            # Save new images
            new_image_ids = image_serializer.save()
            warning_image = WarningImage.objects.create(
                warning=warning,
            )
            warning_image.images.set(new_image_ids)

        # Handle push notification
        send_push_notification = serializer.validated_data.get("send_push_notification")
        push_ok = False
        push_message = None
        if send_push_notification:
            push_ok, push_message = trigger_push_notification(warning)

        # Return the updated warning with notification result
        return_serializer = WarningMessageWithNotificationResultSerializer(
            instance=warning,
            context={
                "push_ok": push_ok,
                "push_message": push_message,
                "media_url": get_media_url(request),
            },
        )
        return Response(return_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        success_response=str,
        examples=[OpenApiExample("Example 1", value="Warning message removed")],
    )
    def delete(self, request, *args, **kwargs):
        warning = self.get_object()
        warning.delete()
        return Response(data="Warning message removed", status=status.HTTP_200_OK)
