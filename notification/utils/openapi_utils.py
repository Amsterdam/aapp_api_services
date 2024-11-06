from drf_spectacular.utils import extend_schema, extend_schema_view


def response_schema(**kwargs):
    def decorator(view):
        extend_schema_view(
            list=extend_schema(responses={200: kwargs["serializer"]}),
            retrieve=extend_schema(responses={200: kwargs["serializer"]}),
            create=extend_schema(responses={201: kwargs["serializer"]}),
            update=extend_schema(responses={200: kwargs["serializer"]}),
            partial_update=extend_schema(responses={200: kwargs["serializer"]}),
        )(view)
        return view

    return decorator
