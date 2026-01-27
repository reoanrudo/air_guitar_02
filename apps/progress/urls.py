"""
Progress URL configuration for VirtuTune

進捗表示画面のURLルーティング
"""

from django.urls import path
from . import views

app_name = "progress"

urlpatterns = [
    path("", views.ProgressView.as_view(), name="progress"),
    path("api/refresh/", views.refresh_stats_api, name="refresh_stats"),
]
