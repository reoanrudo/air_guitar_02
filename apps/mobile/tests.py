"""
Mobileアプリのテスト

QRコード生成、ペアリングセッション管理、モバイルコントローラーのテスト
"""

import json
import uuid
from unittest.mock import Mock, patch

from django.test import Client, TestCase
from django.urls import reverse

from apps.users.models import User
from .services import PairingSessionManager


class PairingSessionManagerTest(TestCase):
    """ペアリングセッションマネージャーのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.user_id = 1
        self.session_id = str(uuid.uuid4())

        # Redisクライアントをモック
        self.redis_patcher = patch("apps.mobile.services.redis.from_url")
        self.mock_redis_from_url = self.redis_patcher.start()
        self.mock_redis_client = Mock()
        self.mock_redis_from_url.return_value = self.mock_redis_client

        self.manager = PairingSessionManager()

    def tearDown(self):
        """テスト終了処理"""
        self.redis_patcher.stop()

    def test_create_session(self):
        """セッション作成のテスト"""
        # Redisのモックを設定
        self.mock_redis_client.setex.return_value = True

        # セッションを作成
        result = self.manager.create_session(self.user_id, self.session_id)

        # 検証
        self.assertTrue(result)
        self.mock_redis_client.setex.assert_called_once()

        # 呼び出し引数を確認
        call_args = self.mock_redis_client.setex.call_args
        key = call_args[0][0]
        self.assertIn(self.session_id, key)
        self.assertEqual(call_args[0][1], 300)  # SESSION_EXPIRY

    def test_validate_session_valid(self):
        """有効なセッションの検証テスト"""
        # Redisのモックを設定
        self.mock_redis_client.exists.return_value = 1

        # 検証
        result = self.manager.validate_session(self.session_id)

        # 検証
        self.assertTrue(result)
        self.mock_redis_client.exists.assert_called_once()

    def test_validate_session_invalid(self):
        """無効なセッションの検証テスト"""
        # Redisのモックを設定（存在しない）
        self.mock_redis_client.exists.return_value = 0

        # 検証
        result = self.manager.validate_session("invalid-session-id")

        # 検証
        self.assertFalse(result)

    def test_get_session(self):
        """セッション情報取得のテスト"""
        # Redisのモックを設定
        session_data = {
            "user_id": self.user_id,
            "status": "waiting",
            "created_at": "2026-01-27T12:00:00Z",
        }
        self.mock_redis_client.get.return_value = json.dumps(session_data)

        # 取得
        session = self.manager.get_session(self.session_id)

        # 検証
        self.assertIsNotNone(session)
        self.assertEqual(session["user_id"], self.user_id)
        self.assertEqual(session["status"], "waiting")
        self.assertIn("created_at", session)

    def test_update_session_status(self):
        """セッションステータス更新のテスト"""
        # Redisのモックを設定
        session_data = {
            "user_id": self.user_id,
            "status": "waiting",
            "created_at": "2026-01-27T12:00:00Z",
        }
        self.mock_redis_client.get.return_value = json.dumps(session_data)
        self.mock_redis_client.ttl.return_value = 300
        self.mock_redis_client.setex.return_value = True

        # ステータスを更新
        result = self.manager.update_session_status(self.session_id, "paired")

        # 検証
        self.assertTrue(result)
        self.mock_redis_client.setex.assert_called()

        # 更新されたデータを確認
        call_args = self.mock_redis_client.setex.call_args
        updated_data = json.loads(call_args[0][2])
        self.assertEqual(updated_data["status"], "paired")

    def test_link_device(self):
        """デバイスリンクのテスト"""
        # Redisのモックを設定
        self.mock_redis_client.exists.return_value = 1
        self.mock_redis_client.setex.return_value = True
        self.mock_redis_client.get.return_value = json.dumps(
            {
                "user_id": self.user_id,
                "status": "waiting",
                "created_at": "2026-01-27T12:00:00Z",
            }
        )
        # TTLモックを追加
        self.mock_redis_client.ttl.return_value = 300

        # デバイスをリンク
        device_id = "test-device-123"
        result = self.manager.link_device(self.session_id, device_id)

        # 検証
        self.assertTrue(result)
        # setexが2回呼ばれる（デバイス保存 + ステータス更新）
        self.assertEqual(self.mock_redis_client.setex.call_count, 2)

    def test_delete_session(self):
        """セッション削除のテスト"""
        # Redisのモックを設定
        self.mock_redis_client.delete.return_value = 2  # 削除されたキーの数

        # 削除
        result = self.manager.delete_session(self.session_id)

        # 検証
        self.assertTrue(result)
        self.mock_redis_client.delete.assert_called_once()


class QRCodeViewTest(TestCase):
    """QRコード生成ビューのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_generate_qr_code_requires_login(self):
        """認証が必要なテスト"""
        # ログアウト
        self.client.logout()

        # アクセス
        response = self.client.get(reverse("mobile:generate_qr_code"))

        # リダイレクトされるはず
        self.assertEqual(response.status_code, 302)

    def test_generate_qr_code_returns_image(self):
        """QRコード画像が返されるテスト"""
        with patch("apps.mobile.views.pairing_manager") as mock_manager:
            mock_manager.create_session.return_value = True

            # アクセス
            response = self.client.get(reverse("mobile:generate_qr_code"))

            # 検証
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertGreater(len(response.content), 0)

    def test_generate_qr_code_creates_session(self):
        """QRコード生成時にセッションが作成されるテスト"""
        with patch("apps.mobile.views.pairing_manager") as mock_manager:
            # アクセス
            self.client.get(reverse("mobile:generate_qr_code"))

            # セッション作成が呼ばれたか確認
            mock_manager.create_session.assert_called_once()


class ControllerViewTest(TestCase):
    """モバイルコントローラービューのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_controller_entry_requires_login(self):
        """認証が必要なテスト"""
        # ログアウト
        self.client.logout()

        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # リダイレクトされるはず
        self.assertEqual(response.status_code, 302)

    def test_controller_entry_renders_template(self):
        """テンプレートがレンダリングされるテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mobile/controller.html")


class ValidateSessionViewTest(TestCase):
    """セッション検証APIのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.session_id = str(uuid.uuid4())

    def test_validate_session_valid(self):
        """有効なセッションの検証テスト"""
        with patch("apps.mobile.views.pairing_manager") as mock_manager:
            mock_manager.validate_session.return_value = True
            mock_manager.get_session.return_value = {
                "user_id": self.user.id,
                "status": "waiting",
            }

            # POSTリクエスト
            response = self.client.post(
                reverse("mobile:validate_session"), {"session_id": self.session_id}
            )

            # 検証
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(
                response.content, {"valid": True, "user_id": self.user.id}
            )

    def test_validate_session_invalid(self):
        """無効なセッションの検証テスト"""
        with patch("apps.mobile.views.pairing_manager") as mock_manager:
            mock_manager.validate_session.return_value = False

            # POSTリクエスト
            response = self.client.post(
                reverse("mobile:validate_session"), {"session_id": "invalid-session"}
            )

            # 検証
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertFalse(data["valid"])

    def test_validate_session_missing_id(self):
        """セッションIDがない場合のテスト"""
        # POSTリクエスト（session_idなし）
        response = self.client.post(reverse("mobile:validate_session"), {})

        # 検証
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertIn("error", data)

    def test_validate_session_wrong_method(self):
        """不正なHTTPメソッドのテスト"""
        # GETリクエスト（POSTのみ許可）
        response = self.client.get(reverse("mobile:validate_session"))

        # 検証
        self.assertEqual(response.status_code, 405)


class MobileControllerUITest(TestCase):
    """モバイルコントローラーUIのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_controller_page_has_all_8_chords(self):
        """8つのコードボタンが表示されるテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertEqual(response.status_code, 200)

        # 8つのコードが含まれているか確認
        chords = ["C", "G", "Am", "F", "D", "E", "Em", "A"]
        for chord in chords:
            self.assertContains(response, f'data-chord="{chord}"')

    def test_controller_page_has_touch_friendly_buttons(self):
        """タッチフレンドリーなボタンがあるテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertContains(response, "chord-btn")
        self.assertContains(response, "mobile.css")

    def test_controller_page_has_connection_status(self):
        """接続ステータス表示があるテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertContains(response, 'id="status-dot"')
        self.assertContains(response, 'id="status-text"')

    def test_controller_page_has_session_input(self):
        """セッションID入力があるテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertContains(response, 'id="session-id"')
        self.assertContains(response, 'id="connect-btn"')


class MobileControllerWebSocketTest(TestCase):
    """モバイルコントローラーWebSocket機能のテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_controller_includes_websocket_script(self):
        """WebSocketスクリプトが含まれているテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertContains(response, "mobile-controller.js")

    def test_controller_has_responsive_design(self):
        """レスポンシブデザインがあるテスト"""
        # アクセス
        response = self.client.get(reverse("mobile:controller_entry"))

        # 検証
        self.assertContains(response, "viewport")
        self.assertContains(response, "user-scalable=no")
