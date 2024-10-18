from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from construction_work.authentication import EntraIDAuthentication
from construction_work.exceptions import MissingProjectIdBody
from construction_work.models import (
    Image,
    Project,
    ProjectManager,
    WarningImage,
    WarningMessage,
)
from construction_work.permissions import (
    IsEditor,
    IsPublisherOnlyReadOwnData,
    IsPublisherOnlyReadOwnProjects,
)
from construction_work.serializers.project_serializers import (
    ProjectListForManageSerializer,
    ProjectManagerCreateResultSerializer,
    ProjectManagerNameEmailSerializer,
    ProjectManagerWithProjectsSerializer,
)
from construction_work.utils.auth_utils import (
    get_manager_type,
    get_project_manager_from_token,
)


class PublisherListCreateView(generics.ListCreateAPIView):
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

    def create(self, request, *args, **kwargs):
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


class PublisherDetailView(generics.RetrieveUpdateDestroyAPIView):
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data="Object removed", status=status.HTTP_200_OK)


class PublisherAssignProjectView(generics.GenericAPIView):
    """
    Assign a project to a publisher.
    """

    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsEditor]

    def post(self, request, pk, *args, **kwargs):
        publisher = get_object_or_404(ProjectManager, pk=pk)
        project_id = request.data.get("project_id")
        if not project_id:
            raise MissingProjectIdBody

        project = get_object_or_404(Project, pk=project_id)
        publisher.projects.add(project)
        return Response(data="Publisher assigned to project", status=status.HTTP_200_OK)


class PublisherUnassignProjectView(generics.GenericAPIView):
    """
    Unassign a project from a publisher.
    """

    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsEditor]

    def delete(self, request, pk, project_id, *args, **kwargs):
        publisher = get_object_or_404(ProjectManager, pk=pk)
        project = get_object_or_404(Project, pk=project_id)
        publisher.projects.remove(project)
        return Response(
            data="Publisher unassigned from project", status=status.HTTP_200_OK
        )


class ProjectListForManageView(generics.ListAPIView):
    """
    Return list of all projects, limit to own projects if request is from publisher.
    """

    serializer_class = ProjectListForManageSerializer
    authentication_classes = [EntraIDAuthentication]
    permission_classes = [IsPublisherOnlyReadOwnProjects]

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
                    Prefetch(
                        "warningimage_set",
                        queryset=WarningImage.objects.prefetch_related(
                            Prefetch(
                                "images", queryset=Image.objects.only("width", "height")
                            )
                        ),
                    )
                ),
            ),
            Prefetch("article_set"),
        )

        return projects
