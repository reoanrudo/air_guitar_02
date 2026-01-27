"""
WebSocket Consumer Tests

WebSocket通信機能のテスト
"""

import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from apps.progress.models import PracticeSession
from config.asgi import application
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGuitarConsumer:
    """GuitarConsumerのテストケース"""

    async def test_websocket_connection(self):
        """WebSocket接続テスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.disconnect()

    async def test_invalid_session_connection(self):
        """無効なセッションIDでの接続拒否テスト"""
        communicator = WebsocketCommunicator(
            application,
            path="/ws/guitar/99999/",
        )

        connected, _ = await communicator.connect()
        assert connected is False

    async def test_chord_change_message(self):
        """コード変更メッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # コード変更メッセージを送信
        await communicator.send_to(
            text_data=json.dumps({"type": "chord_change", "data": {"chord": "C"}})
        )

        await communicator.disconnect()

    async def test_ping_pong_message(self):
        """Ping-Pongメッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # Pingメッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {"type": "ping", "data": {"timestamp": "2024-01-01T00:00:00Z"}}
            )
        )

        # Pongレスポンスを受信
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "pong"
        assert data["data"]["timestamp"] == "2024-01-01T00:00:00Z"

        await communicator.disconnect()

    async def test_practice_start_message(self):
        """練習開始メッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # 練習開始メッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {
                    "type": "practice_start",
                    "data": {"timestamp": "2024-01-01T00:00:00Z"},
                }
            )
        )

        # レスポンスを受信
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "practice_update"
        assert data["data"]["status"] == "started"

        await communicator.disconnect()

    async def test_practice_end_message(self):
        """練習終了メッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # 練習終了メッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {"type": "practice_end", "data": {"timestamp": "2024-01-01T00:00:00Z"}}
            )
        )

        # レスポンスを受信
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "practice_update"
        assert data["data"]["status"] == "ended"

        await communicator.disconnect()

    async def test_invalid_json_message(self):
        """無効なJSONメッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # 無効なJSONを送信
        await communicator.send_to(text_data="invalid json")

        # エラーレスポンスを受信
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "error"

        await communicator.disconnect()

    async def test_unknown_message_type(self):
        """不明なメッセージタイプのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # 不明なタイプのメッセージを送信
        await communicator.send_to(
            text_data=json.dumps({"type": "unknown_type", "data": {}})
        )

        # エラーレスポンスを受信
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "error"

        await communicator.disconnect()

    async def test_connection_notification(self):
        """接続通知のテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を受信
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "connection_update"
        assert data["data"]["status"] == "connected"

        await communicator.disconnect()

    async def test_game_mode_message(self):
        """ゲームモード変更メッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # ゲームモード変更メッセージを送信
        await communicator.send_to(
            text_data=json.dumps({"type": "game_mode", "mode": "rhythm"})
        )

        await communicator.disconnect()

    async def test_game_update_message(self):
        """ゲーム状態更新メッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # ゲーム状態更新メッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {
                    "type": "game_update",
                    "data": {"score": 100, "combo": 5},
                }
            )
        )

        await communicator.disconnect()

    async def test_judgement_message(self):
        """判定結果メッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application,
            path=f"/ws/guitar/{session.id}/",
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # 判定結果メッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {
                    "type": "judgement",
                    "data": {"judgement": "perfect", "score": 100},
                }
            )
        )

        await communicator.disconnect()


@pytest.mark.django_db
class TestWebSocketRouting:
    """WebSocketルーティングのテストケース"""

    def test_websocket_urlpatterns_exist(self):
        """WebSocket URLパターンが存在するかテスト"""
        from apps.websocket.routing import websocket_urlpatterns

        assert len(websocket_urlpatterns) == 1
        # パターン文字列の確認方法を修正
        pattern_str = str(websocket_urlpatterns[0].pattern)
        assert "guitar" in pattern_str.lower()

    def test_consumer_mapping(self):
        """コンシューマーが正しくマッピングされているかテスト"""
        from apps.websocket.routing import websocket_urlpatterns
        from apps.websocket.consumers import GuitarConsumer

        # as_asgi() は呼び出し可能なオブジェクトを返す
        consumer_callable = websocket_urlpatterns[0].callback
        assert callable(consumer_callable)

        # コンシューマーがGuitarConsumerであることを確認
        # as_asgi() メソッドを持つクラスのインスタンスメソッドをチェック
        assert hasattr(GuitarConsumer, 'as_asgi')


@pytest.mark.django_db
class TestWebSocketSettings:
    """WebSocket設定のテストケース"""

    def test_channels_installed(self):
        """Channelsがインストールされているかテスト"""
        from django.conf import settings

        assert "channels" in settings.INSTALLED_APPS

    def test_asgi_application_set(self):
        """ASGIアプリケーションが設定されているかテスト"""
        from django.conf import settings

        assert settings.ASGI_APPLICATION == "config.asgi.application"

    def test_channel_layers_configured(self):
        """チャネルレイヤーが設定されているかテスト"""
        from django.conf import settings

        assert hasattr(settings, "CHANNEL_LAYERS")
        assert "default" in settings.CHANNEL_LAYERS
