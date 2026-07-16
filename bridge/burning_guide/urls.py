from django.urls import path

from bridge.burning_guide.views import advice_view

BASE_PATH = "burning-guide/api/v1"
urlpatterns = [
    path(
        BASE_PATH + "/advice",
        advice_view.BurningGuideAdviceView.as_view(),
        name="burning-guide",
    ),
]
