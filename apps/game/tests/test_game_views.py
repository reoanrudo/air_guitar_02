"""
テスト: ゲームビュー

ゲームモードのビュー機能をテストする
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.game.models import Song, GameSession

User = get_user_model()


class GameListViewTest(TestCase):
    """ゲームリストビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        # テスト用楽曲データを作成
        self.song1 = Song.objects.create(
            name="Test Song 1",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[],
            duration_seconds=60,
            display_order=1,
        )
        self.song2 = Song.objects.create(
            name="Test Song 2",
            artist="Test Artist",
            difficulty=3,
            tempo=140,
            notes=[],
            duration_seconds=90,
            display_order=2,
        )

    def test_game_list_view_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse("game:game_list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/users/login/"))

    def test_game_list_view_returns_200(self):
        """ゲームリストページが正常に表示されることをテスト"""
        response = self.client.get(reverse("game:game_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_list.html")

    def test_game_list_view_displays_songs(self):
        """楽曲が正しく表示されることをテスト"""
        response = self.client.get(reverse("game:game_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Song 1")
        self.assertContains(response, "Test Song 2")
        self.assertContains(response, "Test Artist")

    def test_game_list_view_shows_difficulty(self):
        """難易度が正しく表示されることをテスト"""
        response = self.client.get(reverse("game:game_list"))
        self.assertContains(response, "難易度: 1")
        self.assertContains(response, "難易度: 3")


class GamePlayViewTest(TestCase):
    """ゲームプレイビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[
                {"timing": 0.0, "note": "C", "duration": 1.0},
                {"timing": 1.0, "note": "G", "duration": 1.0},
                {"timing": 2.0, "note": "Am", "duration": 1.0},
            ],
            duration_seconds=60,
            display_order=1,
        )

    def test_game_play_view_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.get(
            reverse("game:game_play", kwargs={"song_id": self.song.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_game_play_view_returns_200(self):
        """ゲームプレイページが正常に表示されることをテスト"""
        response = self.client.get(
            reverse("game:game_play", kwargs={"song_id": self.song.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_play.html")

    def test_game_play_view_contains_song_data(self):
        """楽曲データがコンテキストに含まれることをテスト"""
        response = self.client.get(
            reverse("game:game_play", kwargs={"song_id": self.song.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["song"], self.song)
        self.assertContains(response, "Test Song")
        self.assertContains(response, "Test Artist")

    def test_game_play_view_invalid_song_id(self):
        """無効な楽曲IDで404エラーになることをテスト"""
        response = self.client.get(reverse("game:game_play", kwargs={"song_id": 99999}))
        self.assertEqual(response.status_code, 404)


class SaveGameResultViewTest(TestCase):
    """ゲーム結果保存ビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[],
            duration_seconds=60,
            display_order=1,
        )

    def test_save_game_result_creates_session(self):
        """ゲームセッションが正しく作成されることをテスト"""
        response = self.client.post(
            reverse("game:save_result"),
            data={
                "song_id": self.song.id,
                "score": 1000,
                "max_combo": 10,
                "perfect_count": 5,
                "great_count": 3,
                "good_count": 2,
                "miss_count": 1,
                "accuracy": 85.5,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(GameSession.objects.count(), 1)

        session = GameSession.objects.first()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.song, self.song)
        self.assertEqual(session.score, 1000)
        self.assertEqual(session.max_combo, 10)
        self.assertEqual(session.perfect_count, 5)
        self.assertEqual(session.great_count, 3)
        self.assertEqual(session.good_count, 2)
        self.assertEqual(session.miss_count, 1)
        # View converts percentage to decimal (85.5% -> 0.855)
        self.assertAlmostEqual(session.accuracy, 0.855)

    def test_save_game_result_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.post(
            reverse("game:save_result"),
            data={
                "song_id": self.song.id,
                "score": 1000,
                "max_combo": 10,
                "perfect_count": 5,
                "great_count": 3,
                "good_count": 2,
                "miss_count": 1,
                "accuracy": 85.5,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_save_game_result_invalid_data(self):
        """無効なデータで400エラーになることをテスト"""
        response = self.client.post(
            reverse("game:save_result"),
            data={
                "song_id": self.song.id,
                "score": "invalid",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class GameResultViewTest(TestCase):
    """ゲーム結果ビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[],
            duration_seconds=60,
            display_order=1,
        )

        self.session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=1000,
            max_combo=10,
            perfect_count=5,
            great_count=3,
            good_count=2,
            miss_count=1,
            accuracy=85.5,
        )

    def test_game_result_view_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": self.session.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_game_result_view_returns_200(self):
        """ゲーム結果ページが正常に表示されることをテスト"""
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": self.session.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_result.html")

    def test_game_result_view_displays_stats(self):
        """統計情報が正しく表示されることをテスト"""
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": self.session.id})
        )
        self.assertContains(response, "1000")
        self.assertContains(response, "10")
        self.assertContains(response, "5")
        self.assertContains(response, "3")
        self.assertContains(response, "2")
        self.assertContains(response, "1")
        self.assertContains(response, "85.5")

    def test_game_result_view_unauthorized_session(self):
        """他ユーザーのセッションにアクセスできないことをテスト"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )

        # 他ユーザーのセッションを作成
        other_session = GameSession.objects.create(
            user=other_user,
            song=self.song,
            score=500,
            max_combo=5,
            perfect_count=2,
            great_count=1,
            good_count=1,
            miss_count=1,
            accuracy=70.0,
        )

        # 元のユーザーで他ユーザーのセッションにアクセス
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": other_session.id})
        )
        self.assertEqual(response.status_code, 403)
