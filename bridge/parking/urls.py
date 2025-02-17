from django.urls import path

from bridge.parking import views

urlpatterns = [
    path(
        "parking/api/v1/login",
        views.ParkingAccountLoginView.as_view(),
        name="parking-account-login",
    ),
    path(
        "parking/api/v1/pin-code",
        views.ParkingRequestPinCodeView.as_view(),
        name="parking-request-pin-code",
    ),
    path(
        "parking/api/v1/permits",
        views.ParkingPermitsView.as_view(),
        name="parking-permits",
    ),
    path(
        "parking/api/v1/license-plates",
        views.ParkingLicensePlatesGetView.as_view(),
        name="parking-license-plates-list",
    ),
    path(
        "parking/api/v1/license-plate",
        views.ParkingLicensePlatePostDeleteView.as_view(),
        name="parking-license-plates-post-delete",
    ),
    # path(
    #     "parking/api/v1/license-plate2",
    #     views.ParkingLicensePlatesDeleteView.as_view(),
    #     name="parking-license-plates-delete",
    # ),
]
