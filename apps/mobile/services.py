"""
Mobileアプリのサービス層

QRコードペアリングのセッション管理とデバイス接続処理を提供する
"""

import json
import logging
from typing import Optional

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class PairingSessionManager:
    """
    ペアリングセッション管理クラス

    Redisを使用してペアリングセッションを管理し、
    PCとスマートフォンの接続を仲介する
    """

    # Redisキーのプレフィックス
    SESSION_KEY_PREFIX = "pairing_session:"
    DEVICE_KEY_PREFIX = "paired_device:"

    # セッション有効期限（秒）
    SESSION_EXPIRY = 300  # 5分

    def __init__(self):
        """Redis接続を初期化する"""
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def create_session(self, user_id: int, session_id: str) -> bool:
        """
        ペアリングセッションを作成する

        Args:
            user_id: ユーザーID
            session_id: セッションID（UUID）

        Returns:
            作成成功時はTrue、失敗時はFalse

        Note:
            - セッションは5分で自動的に期限切れになる
            - 同一ユーザーで複数セッションが存在する場合、古いものは上書きされる
        """
        try:
            key = f"{self.SESSION_KEY_PREFIX}{session_id}"
            session_data = {
                "user_id": user_id,
                "status": "waiting",  # waiting, paired, connected
                "created_at": self._get_current_timestamp(),
            }

            # Redisにセッションデータを保存
            self.redis_client.setex(key, self.SESSION_EXPIRY, json.dumps(session_data))

            logger.info(
                f"ペアリングセッション作成: user_id={user_id}, session_id={session_id}"
            )
            return True

        except Exception:
            logger.error(
                f"セッション作成エラー: user_id={user_id}, session_id={session_id}",
                exc_info=True,
                extra={"user_id": user_id, "session_id": session_id},
            )
            return False

    def validate_session(self, session_id: str) -> bool:
        """
        セッションIDを検証する

        Args:
            session_id: 検証するセッションID

        Returns:
            有効なセッションの場合はTrue、無効な場合はFalse

        Note:
            - セッションの存在チェック
            - 有効期限のチェック（RedisのTTLによる自動判定）
        """
        try:
            key = f"{self.SESSION_KEY_PREFIX}{session_id}"
            exists = self.redis_client.exists(key)

            if exists:
                logger.debug(f"セッション検証成功: session_id={session_id}")
            else:
                logger.warning(f"セッション無効または期限切れ: session_id={session_id}")

            return bool(exists)

        except Exception:
            logger.error(
                f"セッション検証エラー: session_id={session_id}",
                exc_info=True,
                extra={"session_id": session_id},
            )
            return False

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        セッション情報を取得する

        Args:
            session_id: セッションID

        Returns:
            セッション情報の辞書、存在しない場合はNone

        Returns例:
            {
                'user_id': 123,
                'status': 'waiting',
                'created_at': '2026-01-27T12:00:00Z'
            }
        """
        try:
            key = f"{self.SESSION_KEY_PREFIX}{session_id}"
            data = self.redis_client.get(key)

            if data:
                return json.loads(data)
            return None

        except Exception:
            logger.error(
                f"セッション取得エラー: session_id={session_id}",
                exc_info=True,
                extra={"session_id": session_id},
            )
            return None

    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        セッションのステータスを更新する

        Args:
            session_id: セッションID
            status: 新しいステータス（'waiting', 'paired', 'connected'）

        Returns:
            更新成功時はTrue、失敗時はFalse
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(
                    f"セッションが存在しないためステータス更新失敗: session_id={session_id}"
                )
                return False

            session["status"] = status
            key = f"{self.SESSION_KEY_PREFIX}{session_id}"

            # TTLを維持したまま更新
            ttl = self.redis_client.ttl(key)
            self.redis_client.setex(
                key, ttl if ttl > 0 else self.SESSION_EXPIRY, json.dumps(session)
            )

            logger.info(
                f"セッションステータス更新: session_id={session_id}, status={status}"
            )
            return True

        except Exception:
            logger.error(
                f"ステータス更新エラー: session_id={session_id}, status={status}",
                exc_info=True,
                extra={"session_id": session_id, "status": status},
            )
            return False

    def link_device(self, session_id: str, device_id: str) -> bool:
        """
        デバイスをセッションにリンクする

        Args:
            session_id: セッションID
            device_id: デバイスID（スマートフォンの識別子）

        Returns:
            リンク成功時はTrue、失敗時はFalse
        """
        try:
            # セッションを検証
            if not self.validate_session(session_id):
                logger.warning(
                    f"無効なセッションへのデバイスリンク試行: session_id={session_id}"
                )
                return False

            # デバイス情報を保存
            key = f"{self.DEVICE_KEY_PREFIX}{session_id}"
            device_data = {
                "device_id": device_id,
                "linked_at": self._get_current_timestamp(),
            }

            self.redis_client.setex(key, self.SESSION_EXPIRY, json.dumps(device_data))

            # セッションステータスを更新
            self.update_session_status(session_id, "paired")

            logger.info(
                f"デバイスリンク成功: session_id={session_id}, device_id={device_id}"
            )
            return True

        except Exception:
            logger.error(
                f"デバイスリンクエラー: session_id={session_id}, device_id={device_id}",
                exc_info=True,
                extra={"session_id": session_id, "device_id": device_id},
            )
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        セッションを削除する

        Args:
            session_id: 削除するセッションID

        Returns:
            削除成功時はTrue、失敗時はFalse
        """
        try:
            session_key = f"{self.SESSION_KEY_PREFIX}{session_id}"
            device_key = f"{self.DEVICE_KEY_PREFIX}{session_id}"

            # セッションとデバイス情報を削除
            self.redis_client.delete(session_key, device_key)

            logger.info(f"セッション削除: session_id={session_id}")
            return True

        except Exception:
            logger.error(
                f"セッション削除エラー: session_id={session_id}",
                exc_info=True,
                extra={"session_id": session_id},
            )
            return False

    def get_user_latest_session(self, user_id: int) -> Optional[dict]:
        """
        ユーザーの最新のセッション情報を取得する

        Args:
            user_id: ユーザーID

        Returns:
            最新のセッション情報の辞書、存在しない場合はNone

        Returns例:
            {
                'session_id': 'uuid-string',
                'user_id': 123,
                'status': 'waiting',
                'created_at': '2026-01-27T12:00:00Z'
            }
        """
        try:
            # Redisでセッションキーをスキャン
            pattern = f"{self.SESSION_KEY_PREFIX}*"
            latest_session = None
            latest_timestamp = None

            for key in self.redis_client.scan_iter(match=pattern):
                data = self.redis_client.get(key)
                if data:
                    session = json.loads(data)
                    if session.get("user_id") == user_id:
                        session_id = key.replace(self.SESSION_KEY_PREFIX, "")
                        session["session_id"] = session_id

                        # 最新のセッションを探す
                        if latest_timestamp is None or session.get("created_at", "") > latest_timestamp:
                            latest_session = session
                            latest_timestamp = session.get("created_at", "")

            if latest_session:
                logger.debug(f"最新セッション取得: user_id={user_id}, session_id={latest_session.get('session_id')}")
            else:
                logger.debug(f"有効なセッションなし: user_id={user_id}")

            return latest_session

        except Exception:
            logger.error(
                f"セッション取得エラー: user_id={user_id}",
                exc_info=True,
                extra={"user_id": user_id},
            )
            return None

    def _get_current_timestamp(self) -> str:
        """
        現在のタイムスタンプをISO形式で取得する

        Returns:
            ISO8601形式のタイムスタンプ文字列
        """
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


# グローバルインスタンス
pairing_manager = PairingSessionManager()
