# Starting point for these settings are the base settings of this app.
# After that, the default settings of the core app will be applied.
# isort wants to change this order, which has to be skipped.
from .base import *  # isort:skip
from core.settings.local import *  # isort:skip

MOCK_SSP_API = os.getenv("MOCK_SSP_API", "false").lower() == "true"

if MOCK_SSP_API:
    from bridge.parking.services import ssp
    from bridge.parking.utils import mock_ssp_api_call

    ssp.ssp_api_call = mock_ssp_api_call
