"""
Tests for ranking app

ランキング機能のテスト
"""

from datetime import timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.game.models import Song, Score, GameSession
from apps.ranking.services import RankingService

User = get_user_model()


class TestRankingService(TestCase):
    """RankingServiceのテスト"""

    def setUp(self):
        """テストデータのセットアップ"""
        # テストユーザー作成
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="testpass123"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@test.com", password="testpass123"
        )

        # テスト楽曲作成
        self.song1 = Song.objects.create(
            name="Test Song 1", artist="Test Artist", difficulty=1, tempo=120
        )
        self.song2 = Song.objects.create(
            name="Test Song 2", artist="Test Artist", difficulty=2, tempo=140
        )

    def test_get_daily_leaderboard_basic(self):
        """日次ランキングが正しく取得できること"""
        today = timezone.now().date()

        # スコアを作成
        Score.objects.create(user=self.user1, song=self.song1, score=1000, date=today)
        Score.objects.create(user=self.user2, song=self.song1, score=1500, date=today)
        Score.objects.create(user=self.user3, song=self.song1, score=800, date=today)

        # ランキングを取得
        leaderboard = RankingService.get_daily_leaderboard(song_id=self.song1.id)

        # 順位を検証
        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0]["score"], 1500)  # 1位
        self.assertEqual(leaderboard[1]["score"], 1000)  # 2位
        self.assertEqual(leaderboard[2]["score"], 800)  # 3位

    def test_get_daily_leaderboard_with_limit(self):
        """limitパラメータで結果数が制限されること"""
        today = timezone.now().date()

        # 5人のユーザーにスコアを作成
        users = [
            User.objects.create_user(
                username=f"testuser{i}", email=f"test{i}@test.com", password="testpass"
            )
            for i in range(5)
        ]

        for i, user in enumerate(users):
            Score.objects.create(
                user=user, song=self.song1, score=1000 + i * 100, date=today
            )

        # 上位3件のみ取得
        leaderboard = RankingService.get_daily_leaderboard(
            song_id=self.song1.id, limit=3
        )

        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0]["score"], 1400)  # 最高スコア

    def test_get_daily_leaderboard_filters_by_song(self):
        """楽曲でフィルタリングされること"""
        today = timezone.now().date()

        # 異なる楽曲のスコアを作成
        Score.objects.create(user=self.user1, song=self.song1, score=1000, date=today)
        Score.objects.create(user=self.user2, song=self.song2, score=2000, date=today)

        # song1のランキングを取得
        leaderboard = RankingService.get_daily_leaderboard(song_id=self.song1.id)

        self.assertEqual(len(leaderboard), 1)
        self.assertEqual(leaderboard[0]["song_id"], self.song1.id)
        self.assertEqual(leaderboard[0]["score"], 1000)

    def test_get_weekly_leaderboard_basic(self):
        """週間ランキングが正しく取得できること"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # 今週のスコアを作成
        Score.objects.create(user=self.user1, song=self.song1, score=1000, date=today)
        Score.objects.create(
            user=self.user2, song=self.song1, score=1500, date=today - timedelta(days=3)
        )

        # 先週のスコア（含まれないはず）
        Score.objects.create(
            user=self.user3,
            song=self.song1,
            score=2000,
            date=week_ago - timedelta(days=1),
        )

        # 週間ランキングを取得
        leaderboard = RankingService.get_weekly_leaderboard(song_id=self.song1.id)

        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]["score"], 1500)
        self.assertEqual(leaderboard[1]["score"], 1000)

    def test_generate_handle_name(self):
        """ハンドルネームが正しく生成されること"""
        handle_name = RankingService.generate_handle_name(self.user1)

        # ハンドルネームの形式を検証
        self.assertIsNotNone(handle_name)
        self.assertIsInstance(handle_name, str)
        self.assertGreater(len(handle_name), 0)

        # ユーザーごとに異なる名前が生成されること
        handle_name2 = RankingService.generate_handle_name(self.user2)
        self.assertNotEqual(handle_name, handle_name2)

    def test_generate_handle_name_consistent(self):
        """同じユーザーには同じハンドルネームが生成されること"""
        handle_name1 = RankingService.generate_handle_name(self.user1)
        handle_name2 = RankingService.generate_handle_name(self.user1)

        self.assertEqual(handle_name1, handle_name2)

    def test_get_user_rank(self):
        """ユーザーの順位が正しく取得できること"""
        today = timezone.now().date()

        # 複数ユーザーのスコアを作成
        Score.objects.create(user=self.user1, song=self.song1, score=1000, date=today)
        Score.objects.create(user=self.user2, song=self.song1, score=1500, date=today)
        Score.objects.create(user=self.user3, song=self.song1, score=800, date=today)

        # user1の順位を取得
        rank = RankingService.get_user_rank(
            user=self.user1, song_id=self.song1.id, period="daily"
        )

        self.assertEqual(rank, 2)  # 2位

    def test_get_user_rank_not_found(self):
        """スコアがないユーザーの順位がNoneになること"""
        rank = RankingService.get_user_rank(
            user=self.user1, song_id=self.song1.id, period="daily"
        )

        self.assertIsNone(rank)


class TestRankingIntegration(TestCase):
    """ランキング機能の統合テスト"""

    def setUp(self):
        """テストデータのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.song = Song.objects.create(
            name="Test Song", artist="Test Artist", difficulty=1, tempo=120
        )

    def test_score_update_after_game(self):
        """ゲーム終了後にスコアが更新されること"""
        today = timezone.now().date()

        # ゲームセッションを作成
        session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=1500,
            max_combo=10,
            perfect_count=5,
            great_count=3,
            good_count=1,
            miss_count=1,
            accuracy=0.9,
        )

        # スコアを更新
        updated_score = RankingService.update_score(
            user=self.user, song=self.song, score=session.score
        )

        # スコアが正しく記録されていることを検証
        self.assertIsNotNone(updated_score)
        self.assertEqual(updated_score.score, 1500)
        self.assertEqual(updated_score.date, today)
        self.assertEqual(updated_score.user, self.user)
        self.assertEqual(updated_score.song, self.song)

    def test_score_update_keeps_highest(self):
        """同じ日の最高スコアが保持されること"""
        # 最初のスコア
        score1 = RankingService.update_score(user=self.user, song=self.song, score=1000)
        self.assertEqual(score1.score, 1000)

        # より高いスコアで更新
        score2 = RankingService.update_score(user=self.user, song=self.song, score=1500)
        self.assertEqual(score2.score, 1500)
        self.assertEqual(score2.id, score1.id)  # 同じレコード

        # より低いスコアで更新（変わらないはず）
        score3 = RankingService.update_score(user=self.user, song=self.song, score=800)
        self.assertEqual(score3.score, 1500)  # 最高スコアが保持される
        self.assertEqual(score3.id, score1.id)  # 同じレコード
