from bridge.parking.urls import urlpatterns as parking_urls
from bridge.proxy.urls import urlpatterns as proxy_urls
from core.urls import get_swagger_paths

BASE_PATH = "bridge/api/v1"

urlpatterns = []
# Proxy views
urlpatterns += proxy_urls
# Parking views
urlpatterns += parking_urls
# Swagger paths
urlpatterns += get_swagger_paths(BASE_PATH)
