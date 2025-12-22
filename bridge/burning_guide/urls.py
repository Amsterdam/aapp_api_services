from django.urls import path

from bridge.burning_guide.views import advice_view, notification_view

BASE_PATH = "burning-guide/api/v1"
urlpatterns = [
    path(
        BASE_PATH + "/advice",
        advice_view.BurningGuideAdviceView.as_view(),
        name="burning-guide",
    ),
    path(
        BASE_PATH + "/notifications",
        notification_view.BurningGuideNotificationCreateView.as_view(),
        name="burning-guide-notification-create",
    ),
    path(
        BASE_PATH + "/notification",
        notification_view.BurningGuideNotificationView.as_view(),
        name="burning-guide-notification",
    ),
]
