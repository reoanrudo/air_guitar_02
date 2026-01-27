"""
Tests for Goal Achievement Feature

目標達成チェック機能のテスト
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.progress.models import PracticeSession
from apps.progress.services import ProgressService

User = get_user_model()


class CheckGoalAchievementTestCase(TestCase):
    """
    check_goal_achievementメソッドのテストケース

    今日の練習時間と目標に基づいて、達成状況を正しく判定することを確認する
    """

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            daily_goal_minutes=30,
        )

    def test_goal_achieved_when_today_minutes_equal_goal(self):
        """
        今日の練習時間が目標と等しい場合、達成と判定されること
        """
        # 今日のセッションを作成（目標の30分）
        now = timezone.now()
        PracticeSession.objects.create(
            user=self.user,
            started_at=now,
            ended_at=now + timedelta(minutes=30),
            duration_minutes=30,
            chords_practiced=["C", "G"],
        )

        result = ProgressService.check_goal_achievement(self.user)

        self.assertTrue(result["achieved"])
        self.assertEqual(result["today_minutes"], 30)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 0)

    def test_goal_achieved_when_today_minutes_exceed_goal(self):
        """
        今日の練習時間が目標を超える場合、達成と判定されること
        """
        # 今日のセッションを作成（目標の30分を超える40分）
        now = timezone.now()
        PracticeSession.objects.create(
            user=self.user,
            started_at=now,
            ended_at=now + timedelta(minutes=40),
            duration_minutes=40,
            chords_practiced=["C", "G", "Am"],
        )

        result = ProgressService.check_goal_achievement(self.user)

        self.assertTrue(result["achieved"])
        self.assertEqual(result["today_minutes"], 40)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 0)

    def test_goal_not_achieved_when_today_minutes_less_than_goal(self):
        """
        今日の練習時間が目標に満たない場合、未達成と判定されること
        """
        # 今日のセッションを作成（目標の30分に満たない20分）
        now = timezone.now()
        PracticeSession.objects.create(
            user=self.user,
            started_at=now,
            ended_at=now + timedelta(minutes=20),
            duration_minutes=20,
            chords_practiced=["C"],
        )

        result = ProgressService.check_goal_achievement(self.user)

        self.assertFalse(result["achieved"])
        self.assertEqual(result["today_minutes"], 20)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 10)

    def test_goal_not_achieved_with_no_sessions_today(self):
        """
        今日の練習セッションがない場合、未達成と判定されること
        """
        result = ProgressService.check_goal_achievement(self.user)

        self.assertFalse(result["achieved"])
        self.assertEqual(result["today_minutes"], 0)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 30)

    def test_multiple_sessions_summed_correctly(self):
        """
        複数のセッションの時間が正しく合計されること
        """
        now = timezone.now()
        # 3つのセッションを作成（合計25分）
        PracticeSession.objects.create(
            user=self.user,
            started_at=now,
            ended_at=now + timedelta(minutes=10),
            duration_minutes=10,
            chords_practiced=["C"],
        )
        PracticeSession.objects.create(
            user=self.user,
            started_at=now + timedelta(hours=1),
            ended_at=now + timedelta(hours=1, minutes=8),
            duration_minutes=8,
            chords_practiced=["G"],
        )
        PracticeSession.objects.create(
            user=self.user,
            started_at=now + timedelta(hours=2),
            ended_at=now + timedelta(hours=2, minutes=7),
            duration_minutes=7,
            chords_practiced=["Am"],
        )

        result = ProgressService.check_goal_achievement(self.user)

        self.assertFalse(result["achieved"])
        self.assertEqual(result["today_minutes"], 25)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 5)

    def test_yesterday_sessions_not_counted(self):
        """
        昨日のセッションが今日の練習時間に含まれないこと
        """
        yesterday = timezone.now() - timedelta(days=1)
        # 昨日のセッション（40分）
        PracticeSession.objects.create(
            user=self.user,
            started_at=yesterday,
            ended_at=yesterday + timedelta(minutes=40),
            duration_minutes=40,
            chords_practiced=["C", "G"],
        )

        # 今日のセッション（10分）
        now = timezone.now()
        PracticeSession.objects.create(
            user=self.user,
            started_at=now,
            ended_at=now + timedelta(minutes=10),
            duration_minutes=10,
            chords_practiced=["Am"],
        )

        result = ProgressService.check_goal_achievement(self.user)

        # 今日の分だけカウントされる
        self.assertFalse(result["achieved"])
        self.assertEqual(result["today_minutes"], 10)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 20)

    def test_only_completed_sessions_counted(self):
        """
        終了していないセッションがカウントされないこと
        """
        now = timezone.now()
        # 完了したセッション（15分）
        PracticeSession.objects.create(
            user=self.user,
            started_at=now,
            ended_at=now + timedelta(minutes=15),
            duration_minutes=15,
            chords_practiced=["C"],
        )
        # 未完了のセッション（終了時刻がない）
        PracticeSession.objects.create(
            user=self.user,
            started_at=now + timedelta(hours=1),
            ended_at=None,
            duration_minutes=0,
            chords_practiced=[],
        )

        result = ProgressService.check_goal_achievement(self.user)

        # 完了したセッションのみカウント
        self.assertFalse(result["achieved"])
        self.assertEqual(result["today_minutes"], 15)
        self.assertEqual(result["goal_minutes"], 30)
        self.assertEqual(result["remaining_minutes"], 15)

    def test_zero_goal_minutes(self):
        """
        目標時間が0分の場合、達成と判定されること
        """
        self.user.daily_goal_minutes = 0
        self.user.save()

        result = ProgressService.check_goal_achievement(self.user)

        self.assertTrue(result["achieved"])
        self.assertEqual(result["today_minutes"], 0)
        self.assertEqual(result["goal_minutes"], 0)
        self.assertEqual(result["remaining_minutes"], 0)
