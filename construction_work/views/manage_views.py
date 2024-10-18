from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from construction_work.authentication import EntraIDAuthentication
from construction_work.models import ProjectManager
from construction_work.permissions import IsEditor, IsPublisherOrReadOwnData
from construction_work.serializers.project_serializers import (
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
            permission_classes = [IsPublisherOrReadOwnData]
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
