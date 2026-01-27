"""
Guitar URL configuration for VirtuTune

仮想ギターアプリのURL設定
"""

from django.urls import path
from apps.guitar import views

app_name = "guitar"

urlpatterns = [
    path("", views.GuitarView.as_view(), name="guitar"),
    path("api/start/", views.start_practice, name="start_practice"),
    path("api/end/", views.end_practice, name="end_practice"),
]
