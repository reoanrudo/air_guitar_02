"""
Pytest configuration for WebSocket tests

WebSocketテスト用のPytest設定とフィクスチャ
"""

import pytest
import asyncio
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from apps.progress.models import PracticeSession
from config.asgi import application

User = get_user_model()


@pytest.fixture
def event_loop():
    """
    イベントループフィクスチャ

    非同期テスト用のイベントループを作成
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user(db):
    """
    テストユーザーフィクスチャ

    Returns:
        User: テスト用ユーザーインスタンス
    """
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def test_practice_session(db, test_user):
    """
    テスト練習セッションフィクスチャ

    Returns:
        PracticeSession: テスト用練習セッションインスタンス
    """
    return PracticeSession.objects.create(user=test_user, target_duration=300)  # 5分


@pytest.fixture
async def websocket_communicator(test_practice_session):
    """
    WebSocketコミュニケーターフィクスチャ

    Args:
        test_practice_session: テスト用練習セッション

    Returns:
        WebsocketCommunicator: WebSocket接続のコミュニケーター
    """
    communicator = WebsocketCommunicator(
        application,
        path=f"/ws/guitar/{test_practice_session.id}/",
    )
    yield communicator

    # クリーンアップ
    if communicator.connected:
        await communicator.disconnect()


@pytest.fixture
def chord_list():
    """
    コードリストフィクスチャ

    Returns:
        list: 利用可能なコードのリスト
    """
    return ["C", "D", "E", "F", "G", "A", "B", "Am", "Dm", "Em"]


# テスト用のカスタムマーカー
def pytest_configure(config):
    """
    Pytestカスタムマーカーの設定
    """
    config.addinivalue_line("markers", "asyncio: マークテストが非同期である")
    config.addinivalue_line("markers", "websocket: WebSocket関連のテスト")
