"""
WebSocket Manual Test Script

WebSocket接続を手動でテストするためのシンプルなスクリプト

使用方法:
    1. Django開発サーバーを起動: python manage.py runserver
    2. 別のターミナルでこのスクリプトを実行: python manual_test.py
"""

import asyncio
import websockets
import json
from datetime import datetime

# テスト用のセッションID（実際のセッションIDに置き換えてください）
SESSION_ID = 1
WS_URL = f"ws://localhost:8000/ws/guitar/{SESSION_ID}/"


async def test_websocket_connection():
    """WebSocket接続テスト"""

    print(f"\n{'=' * 60}")
    print("VirtuTune WebSocket Manual Test")
    print(f"{'=' * 60}\n")

    print(f"接続先: {WS_URL}\n")

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✓ WebSocket接続成功!")

            # 接続通知を受信
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\n[受信] 接続通知: {data}")

            # テスト1: コード変更メッセージ
            print("\n--- テスト1: コード変更 ---")
            chord_change_msg = {"type": "chord_change", "data": {"chord": "C"}}
            await websocket.send(json.dumps(chord_change_msg))
            print(f"[送信] コード変更: {chord_change_msg}")

            # テスト2: Ping-Pong
            print("\n--- テスト2: Ping-Pong ---")
            ping_msg = {
                "type": "ping",
                "data": {"timestamp": datetime.now().isoformat()},
            }
            await websocket.send(json.dumps(ping_msg))
            print(f"[送信] Ping: {ping_msg}")

            response = await websocket.recv()
            data = json.loads(response)
            print(f"[受信] Pong: {data}")

            # テスト3: 練習開始
            print("\n--- テスト3: 練習開始 ---")
            practice_start_msg = {
                "type": "practice_start",
                "data": {"timestamp": datetime.now().isoformat()},
            }
            await websocket.send(json.dumps(practice_start_msg))
            print(f"[送信] 練習開始: {practice_start_msg}")

            # 練習更新通知を受信
            response = await websocket.recv()
            data = json.loads(response)
            print(f"[受信] 練習更新: {data}")

            # 数秒待機
            print("\n--- 3秒間待機 ---")
            await asyncio.sleep(3)

            # テスト4: 練習終了
            print("\n--- テスト4: 練習終了 ---")
            practice_end_msg = {
                "type": "practice_end",
                "data": {"timestamp": datetime.now().isoformat()},
            }
            await websocket.send(json.dumps(practice_end_msg))
            print(f"[送信] 練習終了: {practice_end_msg}")

            # 練習更新通知を受信
            response = await websocket.recv()
            data = json.loads(response)
            print(f"[受信] 練習更新: {data}")

            print("\n" + "=" * 60)
            print("✓ すべてのテストが成功しました!")
            print("=" * 60 + "\n")

    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocketエラー: {e}\n")
        print("ヒント:")
        print("1. Django開発サーバーが起動しているか確認してください")
        print("2. セッションIDが有効か確認してください")
        print("3. Redisサーバーが起動しているか確認してください\n")

    except Exception as e:
        print(f"\n✗ 予期しないエラー: {e}\n")


if __name__ == "__main__":
    print("\nWebSocket手動テストを開始します...")
    print("事前に以下を準備してください:")
    print("1. python manage.py runserver でDjangoサーバーを起動")
    print("2. 有効なセッションIDをスクリプトに設定")

    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\n\nテストが中断されました。\n")
