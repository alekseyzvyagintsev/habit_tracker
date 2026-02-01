from django.urls import path
from rest_framework.routers import DefaultRouter

from tracker.apps import TrackerConfig
from tracker.views import (HabitCreateAPIView,
                           HabitDeleteAPIView,
                           HabitDetailAPIView,
                           HabitListAPIView,
                           HabitUpdateAPIView)

app_name = TrackerConfig.name
router = DefaultRouter()

urlpatterns = [
    path("habit/create/", HabitCreateAPIView.as_view(), name="habit-create"),
    path("habit/<int:pk>/", HabitDetailAPIView.as_view(), name="habit-detail"),
    path("habit/<int:pk>/update/", HabitUpdateAPIView.as_view(), name="habit-update"),
    path("habit/<int:pk>/delete/", HabitDeleteAPIView.as_view(), name="habit-delete"),
    path("habit/list/", HabitListAPIView.as_view(), name="habit-list"),
]
