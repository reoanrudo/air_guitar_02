"""
MobileアプリのURL設定

スマートフォンコントローラーとQRコードペアリングに関連するURLルーティング
"""

from django.urls import path

from . import views

app_name = "mobile"

urlpatterns = [
    # QRコード生成
    path("qr/", views.generate_qr_code, name="generate_qr_code"),
    # セッション検証API
    path("api/validate/", views.validate_session, name="validate_session"),
    # 現在のセッションID取得API
    path("api/current-session/", views.get_current_session, name="get_current_session"),
    # モバイルコントローラーエントリー
    path("controller/", views.controller_entry, name="controller_entry"),
    # HTTPポーリングAPI
    path("api/poll/", views.mobile_poll, name="mobile_poll"),
    # モバイルからのコマンド受信API
    path("api/command/", views.mobile_command, name="mobile_command"),
]
