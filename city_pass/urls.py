from django.urls import path

from city_pass.views import session_views

urlpatterns = [
    path('session/init/', session_views.SessionInitView.as_view(), name="session-init"),
]
