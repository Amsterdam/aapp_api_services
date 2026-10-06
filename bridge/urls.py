from django.urls import path

from bridge.boat_charging.urls import urlpatterns as boatcharging_urls
from bridge.burning_guide.urls import urlpatterns as burning_guide_urls
from bridge.mijnamsterdam.urls import urlpatterns as mijnamsterdam_urls
from bridge.parking.urls import urlpatterns as parking_urls
from bridge.proxy.urls import urlpatterns as proxy_urls
from core.urls import get_swagger_paths
from core.views.health_views import HealthCheckView

BASE_PATH = "bridge/api/v1"

urlpatterns = [
    # health check
    path(
        "bridge/health",
        HealthCheckView.as_view(),
        name="health-check",
    ),
]
# Proxy views
urlpatterns += proxy_urls
# Parking views
urlpatterns += parking_urls
# Burning Guide views
urlpatterns += burning_guide_urls
# MijnAmsterdam views
urlpatterns += mijnamsterdam_urls
# Boat charging views
urlpatterns += boatcharging_urls
# Swagger paths
urlpatterns += get_swagger_paths(BASE_PATH)
