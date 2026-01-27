"""
WebSocket app configuration
"""

from django.apps import AppConfig


class WebsocketConfig(AppConfig):
    """WebSocketアプリケーション設定"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.websocket"
    verbose_name = "WebSocket通信"

    def ready(self):
        """アプリケーション起動時の初期化処理"""
        import apps.websocket.signals  # noqa
