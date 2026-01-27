"""
Progress statistics tests for VirtuTune

進捗統計機能のテスト
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from apps.progress.services import ProgressService
from apps.progress.models import PracticeSession


@pytest.mark.django_db
class TestProgressStatistics:
    """ProgressService統計メソッドのテスト"""

    def test_get_daily_stats_returns_last_7_days(self, django_user_model):
        """get_daily_statsは過去7日間の練習記録を返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 過去7日間のセッションを作成
        today = timezone.now().date()
        for i in range(7):
            session_date = today - timedelta(days=i)
            session_datetime = timezone.make_aware(
                datetime.combine(session_date, datetime.min.time())
            ) + timedelta(hours=12)

            _ = PracticeSession.objects.create(
                user=user,
                started_at=session_datetime,
                ended_at=session_datetime + timedelta(minutes=10 + i),
                duration_minutes=10 + i,
            )

        # 統計を取得
        stats = ProgressService.get_daily_stats(user, days=7)

        # 7日分のデータがあることを確認
        assert len(stats) == 7
        assert all("date" in s for s in stats)
        assert all("minutes" in s for s in stats)

    def test_get_daily_stats_aggregates_same_day_sessions(self, django_user_model):
        """get_daily_statsは同日のセッションを集計する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 同日に複数のセッションを作成
        today = timezone.now().date()
        session_datetime = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )

        PracticeSession.objects.create(
            user=user,
            started_at=session_datetime,
            ended_at=session_datetime + timedelta(minutes=10),
            duration_minutes=10,
        )

        PracticeSession.objects.create(
            user=user,
            started_at=session_datetime + timedelta(hours=1),
            ended_at=session_datetime + timedelta(hours=1, minutes=15),
            duration_minutes=15,
        )

        # 統計を取得
        stats = ProgressService.get_daily_stats(user, days=1)

        # 1日分で合計25分であることを確認
        assert len(stats) == 1
        assert stats[0]["minutes"] == 25

    def test_get_daily_stats_handles_no_sessions(self, django_user_model):
        """get_daily_statsはセッションがない場合に空リストを返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        stats = ProgressService.get_daily_stats(user, days=7)

        assert stats == []

    def test_get_total_stats_returns_comprehensive_stats(self, django_user_model):
        """get_total_statsは包括的な統計を返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=10
        )

        # 今日のセッションを作成
        today = timezone.now().date()
        session_datetime = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )
        PracticeSession.objects.create(
            user=user,
            started_at=session_datetime,
            ended_at=session_datetime + timedelta(minutes=15),
            duration_minutes=15,
        )

        # 統計を取得
        stats = ProgressService.get_total_stats(user)

        # 必要なフィールドがすべて含まれていることを確認
        assert "total_minutes" in stats
        assert "streak_days" in stats
        assert "today_minutes" in stats
        assert "goal_minutes" in stats
        assert "goal_achieved" in stats
        assert "total_hours" in stats

        # 値が正しいことを確認
        assert stats["today_minutes"] == 15
        assert stats["goal_minutes"] == 10
        assert stats["goal_achieved"] is True

    def test_get_total_stats_handles_no_practice_today(self, django_user_model):
        """get_total_statsは今日の練習がない場合に0分を返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=10
        )

        stats = ProgressService.get_total_stats(user)

        assert stats["today_minutes"] == 0
        assert stats["goal_achieved"] is False

    def test_calculate_streak_counts_consecutive_days(self, django_user_model):
        """calculate_streakは連続練習日数を正しく計算する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 過去5日間連続で練習
        today = timezone.now().date()
        for i in range(5):
            session_date = today - timedelta(days=i)
            session_datetime = timezone.make_aware(
                datetime.combine(session_date, datetime.min.time())
            )

            PracticeSession.objects.create(
                user=user,
                started_at=session_datetime,
                ended_at=session_datetime + timedelta(minutes=10),
                duration_minutes=10,
            )

        streak = ProgressService.calculate_streak(user)

        assert streak == 5

    def test_calculate_streak_breaks_on_missed_day(self, django_user_model):
        """calculate_streakは1日空けるとリセットされる"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        today = timezone.now().date()

        # 3日前と2日前に練習（昨日と今日は休み）
        PracticeSession.objects.create(
            user=user,
            started_at=timezone.make_aware(
                datetime.combine(today - timedelta(days=3), datetime.min.time())
            ),
            duration_minutes=10,
        )

        PracticeSession.objects.create(
            user=user,
            started_at=timezone.make_aware(
                datetime.combine(today - timedelta(days=2), datetime.min.time())
            ),
            duration_minutes=10,
        )

        streak = ProgressService.calculate_streak(user)

        # 昨日も今日も練習していないのでストリークは0
        assert streak == 0

    def test_calculate_streak_returns_zero_for_no_practice(self, django_user_model):
        """calculate_streakは練習がない場合に0を返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        streak = ProgressService.calculate_streak(user)

        assert streak == 0

    def test_get_daily_stats_respects_days_parameter(self, django_user_model):
        """get_daily_statsはdaysパラメータを尊重する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 過去10日間のセッションを作成
        today = timezone.now().date()
        for i in range(10):
            session_date = today - timedelta(days=i)
            session_datetime = timezone.make_aware(
                datetime.combine(session_date, datetime.min.time())
            )

            PracticeSession.objects.create(
                user=user, started_at=session_datetime, duration_minutes=10
            )

        # 3日分のみ要求
        stats = ProgressService.get_daily_stats(user, days=3)

        assert len(stats) == 3

    def test_get_total_stats_calculates_total_hours(self, django_user_model):
        """get_total_statsは総時間を時間単位で計算する"""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
            total_practice_minutes=150,  # 2時間30分
        )

        stats = ProgressService.get_total_stats(user)

        assert stats["total_minutes"] == 150
        assert stats["total_hours"] == 2.5

    def test_get_daily_stats_uses_timezone(self, django_user_model):
        """get_daily_statsはタイムゾーンを考慮する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 今日のセッションを作成
        today = timezone.now().date()
        session_datetime = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )

        PracticeSession.objects.create(
            user=user, started_at=session_datetime, duration_minutes=10
        )

        stats = ProgressService.get_daily_stats(user, days=1)

        # 今日の日付が含まれていることを確認
        assert len(stats) == 1
        assert stats[0]["date"] == today.isoformat()
