from django.urls import path

from bridge.burning_guide.views import burning_guide_view

urlpatterns = [
    # Account
    path(
        "burning-guide/api/v1/advice",
        burning_guide_view.BurningGuideView.as_view(),
        name="burning-guide",
    )
]
