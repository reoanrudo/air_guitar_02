"""
WebSocket Consumer Tests

WebSocket通信機能のテスト
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.progress.models import PracticeSession
from apps.websocket.consumers import GuitarConsumer
from django.utils import timezone

User = get_user_model()


class WebSocketSettingsTestCase(TestCase):
    """WebSocket設定のテストケース"""

    def test_channels_installed(self):
        """Channelsがインストールされているかテスト"""
        from django.conf import settings

        self.assertIn("channels", settings.INSTALLED_APPS)

    def test_asgi_application_set(self):
        """ASGIアプリケーションが設定されているかテスト"""
        from django.conf import settings

        self.assertEqual(settings.ASGI_APPLICATION, "config.asgi.application")

    def test_channel_layers_configured(self):
        """チャネルレイヤーが設定されているかテスト"""
        from django.conf import settings

        self.assertIn("CHANNEL_LAYERS", dir(settings))
        self.assertIn("default", settings.CHANNEL_LAYERS)


class WebSocketRoutingTestCase(TestCase):
    """WebSocketルーティングのテストケース"""

    def test_websocket_urlpatterns_exist(self):
        """WebSocket URLパターンが存在するかテスト"""
        from apps.websocket.routing import websocket_urlpatterns

        self.assertEqual(len(websocket_urlpatterns), 1)
        pattern_str = str(websocket_urlpatterns[0].pattern)
        self.assertIn("guitar", pattern_str.lower())

    def test_consumer_mapping(self):
        """コンシューマーが正しくマッピングされているかテスト"""
        from apps.websocket.routing import websocket_urlpatterns

        # コールバックがas_asgi()を通してGuitarConsumerを返すことを確認
        self.assertTrue(callable(websocket_urlpatterns[0].callback))


class WebSocketConsumerTestCase(TestCase):
    """WebSocketコンシューマーのテストケース"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now()
        )

    def test_consumer_class_exists(self):
        """コンシューマークラスが存在するかテスト"""
        self.assertTrue(callable(GuitarConsumer))

    def test_consumer_has_connect_method(self):
        """connectメソッドが存在するかテスト"""
        self.assertTrue(hasattr(GuitarConsumer, "connect"))

    def test_consumer_has_receive_method(self):
        """receiveメソッドが存在するかテスト"""
        self.assertTrue(hasattr(GuitarConsumer, "receive"))

    def test_consumer_has_disconnect_method(self):
        """disconnectメソッドが存在するかテスト"""
        self.assertTrue(hasattr(GuitarConsumer, "disconnect"))

    def test_consumer_has_chord_change_method(self):
        """chord_changeメソッドが存在するかテスト"""
        self.assertTrue(hasattr(GuitarConsumer, "chord_change"))

    def test_consumer_has_practice_update_method(self):
        """practice_updateメソッドが存在するかテスト"""
        self.assertTrue(hasattr(GuitarConsumer, "practice_update"))

    def test_consumer_has_connection_update_method(self):
        """connection_updateメソッドが存在するかテスト"""
        self.assertTrue(hasattr(GuitarConsumer, "connection_update"))


class WebSocketIntegrationTestCase(TestCase):
    """WebSocket統合テストケース"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now()
        )

    def test_session_creation_for_websocket(self):
        """WebSocket用セッション作成テスト"""
        session = PracticeSession.objects.get(id=self.session.id)
        self.assertEqual(session.user, self.user)

    def test_session_id_format(self):
        """セッションID形式テスト"""
        self.assertIsInstance(self.session.id, int)
        self.assertGreater(self.session.id, 0)

    def test_consumer_import(self):
        """コンシューマーインポートテスト"""
        from apps.websocket.consumers import GuitarConsumer

        self.assertIsNotNone(GuitarConsumer)
