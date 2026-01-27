#!/usr/bin/env python
"""
WebSocket Setup Verification Script

WebSocket実装が正しく設定されているかを検証
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import django
from django.conf import settings as django_settings

# Djangoの設定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.websocket.consumers import GuitarConsumer
from apps.websocket.routing import websocket_urlpatterns


def check_channels_installed():
    """Channelsがインストールされているか確認"""
    print("✓ Django Channelsのインストール確認...")
    assert (
        "channels" in django_settings.INSTALLED_APPS
    ), "ChannelsがINSTALLED_APPSにありません"
    print("  - Channels: インストール済み")


def check_asgi_configured():
    """ASGIアプリケーションが設定されているか確認"""
    print("\n✓ ASGIアプリケーションの設定確認...")
    assert hasattr(
        django_settings, "ASGI_APPLICATION"
    ), "ASGI_APPLICATIONが設定されていません"
    assert (
        django_settings.ASGI_APPLICATION == "config.asgi.application"
    ), "ASGI_APPLICATIONの設定が正しくありません"
    print(f"  - ASGI_APPLICATION: {django_settings.ASGI_APPLICATION}")


def check_channel_layers():
    """チャネルレイヤーが設定されているか確認"""
    print("\n✓ チャネルレイヤーの設定確認...")
    assert hasattr(
        django_settings, "CHANNEL_LAYERS"
    ), "CHANNEL_LAYERSが設定されていません"
    assert (
        "default" in django_settings.CHANNEL_LAYERS
    ), "CHANNEL_LAYERS['default']がありません"
    backend = django_settings.CHANNEL_LAYERS["default"]["BACKEND"]
    print(f"  - バックエンド: {backend}")


def check_consumer():
    """コンシューマークラスが正しく実装されているか確認"""
    print("\n✓ GuitarConsumerの実装確認...")

    # 必要なメソッドの存在確認
    required_methods = [
        "connect",
        "receive",
        "disconnect",
        "chord_change",
        "practice_update",
        "connection_update",
    ]

    for method in required_methods:
        assert hasattr(
            GuitarConsumer, method
        ), f"GuitarConsumerに{method}メソッドがありません"
        print(f"  - {method}: 実装済み")


def check_routing():
    """ルーティングが正しく設定されているか確認"""
    print("\n✓ WebSocketルーティングの確認...")
    assert len(websocket_urlpatterns) > 0, "WebSocket URLパターンがありません"

    pattern = websocket_urlpatterns[0]
    pattern_str = str(pattern.pattern)
    print(f"  - パターン: {pattern_str}")
    print(f"  - コンシューマー: {pattern.callback.__name__}")


def check_asgi_application():
    """ASGIアプリケーションファイルの存在確認"""
    print("\n✓ ASGIアプリケーションファイルの確認...")
    asgi_path = django_settings.BASE_DIR / "config" / "asgi.py"
    assert asgi_path.exists(), "asgi.pyが存在しません"
    print(f"  - パス: {asgi_path}")


def check_redis_config():
    """Redis設定の確認"""
    print("\n✓ Redis設定の確認...")
    if hasattr(django_settings, "REDIS_URL"):
        print(f"  - REDIS_URL: {django_settings.REDIS_URL}")
    else:
        print("  - REDIS_URL: デフォルト値を使用")


def main():
    """メインの検証処理"""
    print("\n" + "=" * 60)
    print("VirtuTune WebSocket Setup Verification")
    print("=" * 60 + "\n")

    try:
        check_channels_installed()
        check_asgi_configured()
        check_channel_layers()
        check_consumer()
        check_routing()
        check_asgi_application()
        check_redis_config()

        print("\n" + "=" * 60)
        print("✓ すべてのチェックが成功しました!")
        print("=" * 60 + "\n")

        print("WebSocket実装の準備が完了しました。\n")
        print("次のステップ:")
        print("1. Redisサーバーを起動: redis-server")
        print("2. Djangoサーバーを起動: python manage.py runserver")
        print("3. テストを実行: python manage.py test apps.websocket.test_websocket")
        print("4. 手動テスト: python apps/websocket/manual_test.py\n")

        return 0

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ 検証失敗: {e}")
        print("=" * 60 + "\n")
        return 1

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 予期しないエラー: {e}")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
