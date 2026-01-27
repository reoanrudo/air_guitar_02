"""
URL configuration for ranking app

ランキング機能のURLルーティング
"""

from django.urls import path
from . import views

app_name = "ranking"

urlpatterns = [
    path("", views.RankingView.as_view(), name="ranking"),
    path("achievements/", views.AchievementView.as_view(), name="achievements"),
    path("api/daily/", views.api_daily_leaderboard, name="api_daily"),
    path("api/weekly/", views.api_weekly_leaderboard, name="api_weekly"),
]
