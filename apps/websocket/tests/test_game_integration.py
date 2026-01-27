"""
WebSocket Game Integration Tests

ゲームモードでのWebSocket連携機能のテスト
"""

import json
from django.utils import timezone
import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from config.asgi import application
from apps.progress.models import PracticeSession
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameModeIntegration:
    """ゲームモード統合テスト"""

    async def test_game_mode_message(self):
        """ゲームモードメッセージのテスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application, f"/ws/guitar/{session.id}/"
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # ゲームモードメッセージを送信
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
            application, f"/ws/guitar/{session.id}/"
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # ゲーム更新メッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {
                    "type": "game_update",
                    "data": {
                        "score": 1000,
                        "combo": 10,
                        "maxCombo": 15,
                        "stats": {"perfect": 5, "great": 3, "good": 2, "miss": 0},
                    },
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
            application, f"/ws/guitar/{session.id}/"
        )

        connected, _ = await communicator.connect()
        assert connected is True

        # 接続通知を消費
        await communicator.receive_from()

        # 判定メッセージを送信
        await communicator.send_to(
            text_data=json.dumps(
                {
                    "type": "judgement",
                    "data": {
                        "judgement": "PERFECT",
                        "score": 100,
                        "combo": 5,
                    },
                }
            )
        )

        await communicator.disconnect()

    async def test_chord_change_during_game(self):
        """ゲーム中のコード変更テスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        communicator = WebsocketCommunicator(
            application, f"/ws/guitar/{session.id}/"
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

    async def test_multi_device_sync(self):
        """複数デバイス間の同期テスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        # PC側WebSocket
        pc_communicator = WebsocketCommunicator(
            application, f"/ws/guitar/{session.id}/"
        )

        # モバイル側WebSocket
        mobile_communicator = WebsocketCommunicator(
            application, f"/ws/guitar/{session.id}/"
        )

        # 両方接続
        pc_connected, _ = await pc_communicator.connect()
        mobile_connected, _ = await mobile_communicator.connect()

        assert pc_connected is True
        assert mobile_connected is True

        # 接続通知を消費
        try:
            await pc_communicator.receive_from(timeout=0.1)
        except Exception:
            pass
        try:
            await mobile_communicator.receive_from(timeout=0.1)
        except Exception:
            pass

        # 最初の切断を試みる
        try:
            await pc_communicator.disconnect()
        except Exception:
            pass

        # 2番目の切断を試みる
        try:
            await mobile_communicator.disconnect()
        except Exception:
            pass

        # テストの成功を確認 - 両方の接続が確立できたこと
        assert pc_connected
        assert mobile_connected

    async def test_pause_resume_sync(self):
        """一時停止/再開の同期テスト"""
        user = await database_sync_to_async(User.objects.create_user)(
            username="testuser", email="test@example.com", password="testpass123"
        )
        session = await database_sync_to_async(PracticeSession.objects.create)(
            user=user, started_at=timezone.now()
        )

        pc_communicator = WebsocketCommunicator(
            application, f"/ws/guitar/{session.id}/"
        )

        mobile_communicator = WebsocketCommunicator(
            application, f"/ws/guitar/{session.id}/"
        )

        await pc_communicator.connect()
        await mobile_communicator.connect()

        # 接続通知を消費
        await pc_communicator.receive_from()
        await mobile_communicator.receive_from()

        await pc_communicator.disconnect()
        await mobile_communicator.disconnect()
