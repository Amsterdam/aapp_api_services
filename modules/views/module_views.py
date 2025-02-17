from django.db.models import ProtectedError
from rest_framework import generics, status
from rest_framework.response import Response

from core.exceptions import InputDataException, NoInputDataException
from core.utils.openapi_utils import extend_schema_for_api_key as extend_schema
from modules.exceptions import ModuleNotFoundException, ModuleProtectedException
from modules.models import Module
from modules.serializers.module_serializers import (
    ModuleSerializer,
    ModuleWithVersionSerializer,
)
from modules.views.utils import slug_status_in_releases, version_number_as_list


class ModuleCreateView(generics.CreateAPIView):
    """
    Create module

    slug: (string) The human-readable identifier for the module. Example: construction-work.
    status (integer): The status of the module. This allows deactivating all of its versions in all releases at once.

    Allowed status values: [0|1]
    """

    serializer_class = ModuleSerializer

    @extend_schema(
        success_response=ModuleSerializer,
        exceptions=[InputDataException],
        description="Creates a new module.",
    )
    def post(self, request, *args, **kwargs):
        data = dict(request.data)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            raise InputDataException(serializer.errors)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieves details for a module by slug. Returns all the module versions for that slug
    and the status of that module across all releases.
    PATCH: Changes the status for a module slug.
    DELETE: Deletes a module by slug.

    slug: (string): The human-readable identifier for the module. Example: construction-work.
    status (integer): The status of the module. This allows deactivating all of its versions in all releases at once.

    Allowed status values: [0|1]
    """

    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    http_method_names = ["get", "patch", "delete"]
    serializer_class = ModuleWithVersionSerializer

    def get_queryset(self):
        return Module.objects.all()

    def get_object(self):
        slug = self.kwargs.get(self.lookup_url_kwarg)
        try:
            module = Module.objects.get(slug=slug)
            return module
        except Module.DoesNotExist:
            return None

    @extend_schema(
        success_response=ModuleWithVersionSerializer,
        exceptions=[ModuleNotFoundException],
        description=(
            "Retrieves details for a module by slug. Returns all the module versions for that slug "
            "and the status of that module across all releases."
        ),
    )
    def get(self, request, *args, **kwargs):
        module = self.get_object()
        slug = self.kwargs.get(self.lookup_url_kwarg)
        if module is None:
            raise ModuleNotFoundException(f"Module with slug '{slug}' not found.")
        context = {"status_in_releases": slug_status_in_releases(slug)}
        serializer = ModuleWithVersionSerializer(instance=module, context=context)
        serializer_data = serializer.data

        def version_key(_module):
            return version_number_as_list(_module["version"])

        # Sort versions on version in result
        serializer_data["versions"] = sorted(
            serializer_data["versions"], key=version_key, reverse=True
        )

        return Response(serializer_data, status=status.HTTP_200_OK)

    @extend_schema(
        success_response=ModuleSerializer,
        exceptions=[NoInputDataException, ModuleNotFoundException, InputDataException],
        description="Changes the status for a module slug.",
    )
    def patch(self, request, *args, **kwargs):
        slug = self.kwargs.get(self.lookup_url_kwarg)
        data = dict(request.data)
        if not data:
            raise NoInputDataException
        if data.get("slug") is None:
            data["slug"] = slug

        module = self.get_object()
        if module is None:
            raise ModuleNotFoundException(f"Module with slug '{slug}' not found.")

        serializer = ModuleSerializer(instance=module, data=data)
        if not serializer.is_valid():
            raise InputDataException(serializer.errors)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        success_response=None,
        exceptions=[ModuleNotFoundException, ModuleProtectedException],
        description="Deletes a module by slug.",
    )
    def delete(self, request, *args, **kwargs):
        slug = self.kwargs.get(self.lookup_url_kwarg)
        module = self.get_object()
        if module is None:
            raise ModuleNotFoundException(f"Module with slug '{slug}' not found.")
        try:
            module.delete()
        except ProtectedError:
            raise ModuleProtectedException(
                "Module cannot be deleted while it has versions"
            )
        return Response(status=status.HTTP_200_OK)
