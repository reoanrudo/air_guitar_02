"""
WebSocket consumers for VirtuTune

スマホとPCのリアルタイム通信のためのコンシューマー
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.progress.models import PracticeSession
from apps.mobile.services import pairing_manager

logger = logging.getLogger(__name__)


class GuitarConsumer(AsyncWebsocketConsumer):
    """
    仮想ギター用WebSocketコンシューマー

    スマホとPCの間でリアルタイム通信を行う
    - コード変更イベント
    - 練習セッション状態の同期
    - 接続管理
    """

    async def connect(self):
        """接続確立時の処理"""
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"guitar_{self.session_id}"
        self.user = self.scope["user"].is_authenticated and self.scope["user"] or None

        # セッションの存在確認
        if not await self._validate_session():
            logger.warning(f"無効なセッションID: {self.session_id}")
            await self.close(code=4000)
            return

        # チャネルグループに参加
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # 接続を通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "connection_update",
                "status": "connected",
                "user_id": self.user.id if self.user else None,
            },
        )

        await self.accept()

        logger.info(
            f"WebSocket接続確立: session_id={self.session_id}, "
            f"user_id={self.user.id if self.user else None}"
        )

    async def receive(self, text_data):
        """
        メッセージ受信時の処理

        サポートされるメッセージタイプ:
        - chord_change: コード変更
        - practice_start: 練習開始
        - practice_end: 練習終了
        - game_mode: ゲームモード設定
        - game_update: ゲーム状態更新
        - judgement: 判定結果
        - ping: 接続確認
        - camera_frame: カメラフレーム送信（PCからモバイルへ）
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if message_type == "chord_change":
                await self._handle_chord_change(text_data_json)
            elif message_type == "practice_start":
                await self._handle_practice_start(text_data_json)
            elif message_type == "practice_end":
                await self._handle_practice_end(text_data_json)
            elif message_type == "game_mode":
                await self._handle_game_mode(text_data_json)
            elif message_type == "game_update":
                await self._handle_game_update(text_data_json)
            elif message_type == "judgement":
                await self._handle_judgement(text_data_json)
            elif message_type == "ping":
                await self._handle_ping(text_data_json)
            elif message_type == "camera_frame":
                await self._handle_camera_frame(text_data_json)
            else:
                logger.warning(f"不明なメッセージタイプ: {message_type}")
                await self._send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"JSONデコードエラー: {e}")
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"メッセージ処理エラー: {e}", exc_info=True)
            await self._send_error("Internal server error")

    async def _handle_chord_change(self, data):
        """コード変更イベントの処理"""
        chord = data.get("data", {}).get("chord")

        if not chord:
            await self._send_error("Chord is required")
            return

        # チャネルグループにコード変更イベントを送信
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chord_change",
                "chord": chord,
                "sender_id": self.channel_name,
            },
        )

        logger.info(f"コード変更: session_id={self.session_id}, chord={chord}")

    async def _handle_practice_start(self, data):
        """練習開始イベントの処理"""
        # グループに通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "practice_update",
                "status": "started",
                "timestamp": data.get("data", {}).get("timestamp"),
            },
        )

        logger.info(f"練習開始: session_id={self.session_id}")

    async def _handle_practice_end(self, data):
        """練習終了イベントの処理"""
        # グループに通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "practice_update",
                "status": "ended",
                "timestamp": data.get("data", {}).get("timestamp"),
            },
        )

        logger.info(f"練習終了: session_id={self.session_id}")

    async def _handle_ping(self, data):
        """Pingメッセージの処理"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "pong",
                    "data": {"timestamp": data.get("data", {}).get("timestamp")},
                }
            )
        )

    async def _handle_camera_frame(self, data):
        """
        カメラフレームの処理

        PCから送信されたカメラフレームをモバイルコントローラーに転送する
        """
        frame_data = data.get("data", {})

        # チャネルグループにカメラフレームを送信（送信者以外）
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "camera_frame",
                "data": frame_data,
                "sender_id": self.channel_name,
            },
        )

        logger.debug(f"カメラフレーム転送: session_id={self.session_id}")

    async def _handle_game_mode(self, data):
        """ゲームモード設定の処理"""
        mode = data.get("mode")

        # グループにゲームモード変更を通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_mode",
                "mode": mode,
                "sender_id": self.channel_name,
            },
        )

        logger.info(f"ゲームモード変更: session_id={self.session_id}, mode={mode}")

    async def _handle_game_update(self, data):
        """ゲーム状態更新の処理"""
        update_data = data.get("data", {})

        # グループにゲーム状態更新を通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_update",
                "data": update_data,
                "sender_id": self.channel_name,
            },
        )

    async def _handle_judgement(self, data):
        """判定結果の処理"""
        judgement_data = data.get("data", {})

        # グループに判定結果を通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "judgement",
                "data": judgement_data,
                "sender_id": self.channel_name,
            },
        )

    async def chord_change(self, event):
        """コード変更イベントの送信"""
        # 送信者以外に送信
        if event.get("sender_id") != self.channel_name:
            await self.send(
                text_data=json.dumps(
                    {"type": "chord_change", "data": {"chord": event["chord"]}}
                )
            )

    async def practice_update(self, event):
        """練習状態更新イベントの送信"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "practice_update",
                    "data": {
                        "status": event["status"],
                        "timestamp": event.get("timestamp"),
                    },
                }
            )
        )

    async def connection_update(self, event):
        """接続状態更新イベントの送信"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_update",
                    "data": {
                        "status": event["status"],
                        "user_id": event.get("user_id"),
                    },
                }
            )
        )

    async def game_mode(self, event):
        """ゲームモード変更イベントの送信"""
        # 送信者以外に送信
        if event.get("sender_id") != self.channel_name:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "game_mode",
                        "mode": event["mode"],
                    }
                )
            )

    async def game_update(self, event):
        """ゲーム状態更新イベントの送信"""
        # 送信者以外に送信
        if event.get("sender_id") != self.channel_name:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "game_update",
                        "data": event["data"],
                    }
                )
            )

    async def judgement(self, event):
        """判定結果イベントの送信"""
        # 送信者以外に送信
        if event.get("sender_id") != self.channel_name:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "judgement",
                        "data": event["data"],
                    }
                )
            )

    async def camera_frame(self, event):
        """
        カメラフレームイベントの送信

        PCから送信されたカメラフレームをモバイルコントローラーに転送する
        """
        # 送信者以外に送信（PCが自分の送信したフレームを受け取らないように）
        if event.get("sender_id") != self.channel_name:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "camera_frame",
                        "data": event.get("data", {}),
                    }
                )
            )

    async def _send_error(self, message):
        """エラーメッセージを送信"""
        await self.send(
            text_data=json.dumps({"type": "error", "data": {"message": message}})
        )

    async def _validate_session(self):
        """
        セッションの有効性を検証

        Returns:
            bool: セッションが有効な場合はTrue

        Note:
            QRコードペアリングのセッションIDはRedisで管理されているため、
            pairing_managerで検証する
        """
        try:
            # Redisのペアリングセッションで検証
            is_valid = await database_sync_to_async(pairing_manager.validate_session)(
                self.session_id
            )

            if is_valid:
                logger.info(f"セッション検証成功: session_id={self.session_id}")
            else:
                logger.warning(f"セッション検証失敗: session_id={self.session_id}")

            return is_valid

        except Exception as e:
            logger.error(
                f"セッション検証エラー: session_id={self.session_id}",
                exc_info=True,
            )
            return False

    async def disconnect(self, close_code):
        """切断時の処理"""
        try:
            # チャネルグループから退出
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

            # 切断を通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "connection_update",
                    "status": "disconnected",
                    "user_id": self.user.id if self.user else None,
                },
            )

            logger.info(
                f"WebSocket切断: session_id={self.session_id}, "
                f"user_id={self.user.id if self.user else None}, "
                f"code={close_code}"
            )

        except Exception as e:
            logger.error(f"切断処理エラー: {e}", exc_info=True)
