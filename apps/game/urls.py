"""
URL configuration for game app

ゲーム機能のURLルーティングを定義する
"""

from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    # ゲーム一覧画面
    path("", views.GameListView.as_view(), name="game_list"),
    # ゲームプレイ画面
    path("play/<int:song_id>/", views.GamePlayView.as_view(), name="game_play"),
    # ゲーム結果画面
    path(
        "result/<int:session_id>/", views.GameResultView.as_view(), name="game_result"
    ),
    # ゲーム結果保存API
    path("api/save/", views.save_game_result, name="save_result"),
]
