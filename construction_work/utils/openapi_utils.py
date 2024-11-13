from rest_framework.exceptions import PermissionDenied

from core.views.extend_schema import custom_extend_schema


def extend_schema_for_entra(
    success_response=None, exceptions=None, additional_params=None, **kwargs
):
    return custom_extend_schema(
        default_exceptions=[PermissionDenied],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=additional_params,
        **kwargs
    )

class AutoExtendSchemaMixin:
    """
    Auto decorate HTTP methods with extend_schema_for_entra using the serializer_class.
    Skip if method is already decorated with this function.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Get methods from base classes to compare later
        base_methods = {}
        for base in cls.__bases__:
            for attr_name in dir(base):
                attr = getattr(base, attr_name)
                if callable(attr):
                    base_methods[attr_name] = attr

        # Loop through HTTP methods and apply the decorator if not overridden
        for http_method in [
            "get",
            "retrieve",
            "post",
            "create",
            "put",
            "update",
            "patch",
            "partial_update",
            "delete",
            "destroy",
        ]:
            method = getattr(cls, http_method, None)
            if method is None:
                continue

            # Check if the method is already decorated with `extend_schema` or `extend_schema_for_entra`
            if hasattr(method, "_schema_extended"):
                # Method is already decorated; skip auto-decoration
                continue

            decorated_method = extend_schema_for_entra(
                success_response=cls.serializer_class
            )(method)

            setattr(cls, http_method, decorated_method)
