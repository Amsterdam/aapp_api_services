from bridge.burning_guide.urls import urlpatterns as burning_guide_urls
from bridge.mijnamsterdam.urls import urlpatterns as mijnamsterdam_urls
from bridge.parking.urls import urlpatterns as parking_urls
from bridge.proxy.urls import urlpatterns as proxy_urls
from core.urls import get_swagger_paths

BASE_PATH = "bridge/api/v1"

urlpatterns = []
# Proxy views
urlpatterns += proxy_urls
# Parking views
urlpatterns += parking_urls
# Burning Guide views
urlpatterns += burning_guide_urls
# MijnAmsterdam views
urlpatterns += mijnamsterdam_urls
# Swagger paths
urlpatterns += get_swagger_paths(BASE_PATH)
