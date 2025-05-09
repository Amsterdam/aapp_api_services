from bridge.parking.serializers.transaction_serializers import (
    TransactionResponseSerializer,
    TransactionsListPaginatedResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.views.base_ssp_view import BaseSSPView, ssp_openapi_decorator


class TransactionsListView(BaseSSPView):
    """
    Get transactions from SSP API
    """

    response_serializer_class = TransactionResponseSerializer
    response_serializer_many = True
    response_key_selection = "data"
    ssp_endpoint = SSPEndpoint.TRANSACTIONS
    ssp_http_method = "get"
    requires_access_token = True
    paginated = True

    @ssp_openapi_decorator(
        response_serializer_class=TransactionsListPaginatedResponseSerializer,
        requires_access_token=True,
        paginated=True,
    )
    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)
