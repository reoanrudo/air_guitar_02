"""
Tests for Achievement Service

実績解除サービスのテスト
"""

from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.game.models import Song, GameSession, Achievement, UserAchievement
from apps.progress.models import PracticeSession
from apps.ranking.services import AchievementUnlockService

User = get_user_model()


class TestAchievementUnlockService(TestCase):
    """AchievementUnlockServiceのテスト"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.song = Song.objects.create(
            name="Test Song", artist="Test Artist", difficulty=1, tempo=120
        )

    def test_check_achievements_first_play(self):
        """初回プレイ実績のテスト"""
        # ゲームセッションを作成
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=100,
            max_combo=5,
            perfect_count=5,
            great_count=5,
            good_count=0,
            miss_count=0,
            accuracy=0.8,
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # 初回プレイ実績が解除されていることを確認
        self.assertEqual(len(unlocked), 1)
        self.assertEqual(unlocked[0].name, "FIRST_PLAY")

        # UserAchievementが作成されていることを確認
        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user, achievement__name="FIRST_PLAY"
            ).exists()
        )

    def test_check_achievements_perfect_play(self):
        """パーフェクトプレイ実績のテスト"""
        # ゲームセッションを作成（100%精度）
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=1000,
            max_combo=20,
            perfect_count=20,
            great_count=0,
            good_count=0,
            miss_count=0,
            accuracy=1.0,  # 100%
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # パーフェクトプレイ実績が解除されていることを確認
        achievement_names = [a.name for a in unlocked]
        self.assertIn("PERFECT_PLAY", achievement_names)

    def test_check_achievements_streak_7(self):
        """7日連続練習実績のテスト"""
        # 過去7日間の練習セッションを作成
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            PracticeSession.objects.create(
                user=self.user,
                started_at=date,
                ended_at=date + timedelta(minutes=30),
                duration_minutes=30,
                chords_practiced=["C", "G"],
            )

        # ユーザーのストリークを更新
        self.user.streak_days = 7
        self.user.save()

        # ゲームセッションを作成
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=100,
            max_combo=5,
            perfect_count=5,
            great_count=0,
            good_count=5,
            miss_count=0,
            accuracy=0.8,
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # ストリーク実績が解除されていることを確認
        achievement_names = [a.name for a in unlocked]
        self.assertIn("STREAK_7", achievement_names)

    def test_check_achievements_score_1000(self):
        """スコア1000達成実績のテスト"""
        # ゲームセッションを作成（スコア1000以上）
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=1500,
            max_combo=20,
            perfect_count=20,
            great_count=5,
            good_count=0,
            miss_count=0,
            accuracy=0.9,
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # スコア1000実績が解除されていることを確認
        achievement_names = [a.name for a in unlocked]
        self.assertIn("SCORE_1000", achievement_names)

    def test_check_achievements_combo_master(self):
        """コンボマスター実績のテスト"""
        # ゲームセッションを作成（50コンボ以上）
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=500,
            max_combo=50,  # 50コンボ
            perfect_count=30,
            great_count=20,
            good_count=0,
            miss_count=0,
            accuracy=0.85,
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # コンボマスター実績が解除されていることを確認
        achievement_names = [a.name for a in unlocked]
        self.assertIn("COMBO_MASTER", achievement_names)

    def test_check_achievements_practice_hour(self):
        """1時間練習実績のテスト"""
        # ユーザーの総練習時間を設定（60分以上）
        self.user.total_practice_minutes = 65
        self.user.save()

        # ゲームセッションを作成
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=100,
            max_combo=5,
            perfect_count=5,
            great_count=0,
            good_count=5,
            miss_count=0,
            accuracy=0.8,
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # 練習時間実績が解除されていることを確認
        achievement_names = [a.name for a in unlocked]
        self.assertIn("PRACTICE_HOUR", achievement_names)

    def test_check_achievements_no_duplicate_unlock(self):
        """実績の重複解除防止テスト"""
        # 既に実績を解除している状態を作成
        achievement = Achievement.objects.get(name="FIRST_PLAY")
        UserAchievement.objects.create(user=self.user, achievement=achievement)

        # ゲームセッションを作成
        game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=100,
            max_combo=5,
            perfect_count=5,
            great_count=0,
            good_count=5,
            miss_count=0,
            accuracy=0.8,
        )

        # 実績チェック
        unlocked = AchievementUnlockService.check_achievements(
            self.user, game_session, None
        )

        # 初回プレイ実績が重複して解除されていないことを確認
        achievement_names = [a.name for a in unlocked]
        self.assertNotIn("FIRST_PLAY", achievement_names)

    def test_unlock_achievement(self):
        """実績解除メソッドのテスト"""
        achievement = Achievement.objects.get(name="FIRST_PLAY")

        # 実績を解除
        result = AchievementUnlockService.unlock_achievement(self.user, "FIRST_PLAY")

        # 解除に成功していることを確認
        self.assertTrue(result)

        # UserAchievementが作成されていることを確認
        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user, achievement=achievement
            ).exists()
        )

    def test_unlock_achievement_already_unlocked(self):
        """既に解除済みの実績解除テスト"""
        achievement = Achievement.objects.get(name="FIRST_PLAY")

        # 先に実績を解除
        UserAchievement.objects.create(user=self.user, achievement=achievement)

        # 再度実績を解除しようとする
        result = AchievementUnlockService.unlock_achievement(self.user, "FIRST_PLAY")

        # Falseが返されることを確認
        self.assertFalse(result)

    def test_unlock_achievement_not_found(self):
        """存在しない実績の解除テスト"""
        # 存在しない実績を解除しようとする
        result = AchievementUnlockService.unlock_achievement(
            self.user, "NON_EXISTENT_ACHIEVEMENT"
        )

        # Falseが返されることを確認
        self.assertFalse(result)

    def test_get_user_achievements(self):
        """ユーザー実績取得テスト"""
        # 複数の実績を解除
        AchievementUnlockService.unlock_achievement(self.user, "FIRST_PLAY")
        AchievementUnlockService.unlock_achievement(self.user, "SCORE_1000")

        # ユーザー実績を取得
        achievements = AchievementUnlockService.get_user_achievements(self.user)

        # 2つの実績が取得されていることを確認
        self.assertEqual(len(achievements), 2)

        # 実績が正しい順序で並んでいることを確認（解除日時の降順）
        self.assertEqual(achievements[0].achievement.name, "SCORE_1000")
        self.assertEqual(achievements[1].achievement.name, "FIRST_PLAY")

    def test_get_user_achievements_empty(self):
        """実績なしのユーザー実績取得テスト"""
        # 実績を解除していないユーザーの実績を取得
        achievements = AchievementUnlockService.get_user_achievements(self.user)

        # 空のリストが返されることを確認
        self.assertEqual(len(achievements), 0)

    def test_get_achievement_progress(self):
        """実績進捗取得テスト"""
        # 実績を解除
        AchievementUnlockService.unlock_achievement(self.user, "FIRST_PLAY")

        # 実績進捗を取得
        progress = AchievementUnlockService.get_achievement_progress(self.user)

        # 進捗が正しく計算されていることを確認
        self.assertEqual(progress["total"], 6)  # 全実績数
        self.assertEqual(progress["unlocked"], 1)  # 解除数
        self.assertAlmostEqual(progress["percentage"], 16.67, places=2)  # 16.67%
