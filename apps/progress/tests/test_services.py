"""
ProgressService tests for VirtuTune

練習記録サービスのテスト
"""

import pytest
from datetime import datetime
from django.utils import timezone
from apps.progress.services import ProgressService
from apps.progress.models import PracticeSession


@pytest.mark.django_db
class TestProgressService:
    """ProgressServiceのテスト"""

    def test_start_session_creates_new_practice_session(self, django_user_model):
        """start_sessionは新しい練習セッションを作成する"""
        # テストユーザーを作成
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=5
        )

        # セッションを開始
        session = ProgressService.start_session(user)

        # セッションが正しく作成されたことを確認
        assert session is not None
        assert session.user == user
        assert session.started_at is not None
        assert session.ended_at is None
        assert session.duration_minutes == 0
        assert session.chords_practiced == []
        assert session.goal_achieved is None

    def test_start_session_saves_to_database(self, django_user_model):
        """start_sessionはセッションをデータベースに保存する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # セッションを開始
        session = ProgressService.start_session(user)

        # データベースから取得して確認
        saved_session = PracticeSession.objects.get(id=session.id)
        assert saved_session.id == session.id
        assert saved_session.user == user

    def test_calculate_duration_returns_correct_minutes(self):
        """calculate_durationは正しい練習時間（分）を返す"""
        # 開始時刻と終了時刻を設定
        started_at = timezone.make_aware(datetime(2026, 1, 27, 10, 0, 0))
        ended_at = timezone.make_aware(datetime(2026, 1, 27, 10, 5, 30))

        # 練習時間を計算（5分30秒 = 5分）
        duration = ProgressService.calculate_duration(started_at, ended_at)

        assert duration == 5

    def test_calculate_duration_rounds_down_seconds(self):
        """calculate_durationは秒数を切り捨てる"""
        started_at = timezone.make_aware(datetime(2026, 1, 27, 10, 0, 0))
        ended_at = timezone.make_aware(datetime(2026, 1, 27, 10, 5, 59))

        # 5分59秒 = 5分（切り捨て）
        duration = ProgressService.calculate_duration(started_at, ended_at)

        assert duration == 5

    def test_calculate_duration_handles_exact_minutes(self):
        """calculate_durationは正確な分数を処理する"""
        started_at = timezone.make_aware(datetime(2026, 1, 27, 10, 0, 0))
        ended_at = timezone.make_aware(datetime(2026, 1, 27, 10, 10, 0))

        duration = ProgressService.calculate_duration(started_at, ended_at)

        assert duration == 10

    def test_end_session_updates_session_fields(self, django_user_model):
        """end_sessionはセッションフィールドを更新する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=5
        )

        # セッションを作成
        session = ProgressService.start_session(user)

        # セッションを終了
        chords = ["C", "G", "Am"]
        duration_minutes = 10
        updated_session = ProgressService.end_session(session, chords, duration_minutes)

        # フィールドが更新されたことを確認
        assert updated_session.ended_at is not None
        assert updated_session.duration_minutes == duration_minutes
        assert updated_session.chords_practiced == chords
        assert updated_session.goal_achieved is True  # 10分 >= 5分

    def test_end_session_updates_user_stats(self, django_user_model):
        """end_sessionはユーザー統計を更新する"""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
            daily_goal_minutes=5,
            total_practice_minutes=100,
        )

        # セッションを作成して終了
        session = ProgressService.start_session(user)
        chords = ["C", "G"]
        duration_minutes = 15

        ProgressService.end_session(session, chords, duration_minutes)

        # ユーザーをリロードして確認
        user.refresh_from_db()
        assert user.total_practice_minutes == 115  # 100 + 15
        assert user.last_practice_date is not None

    def test_end_session_sets_goal_achieved_true_when_goal_met(self, django_user_model):
        """end_sessionは目標達成時にgoal_achievedをTrueにする"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=5
        )

        session = ProgressService.start_session(user)
        chords = ["C"]
        duration_minutes = 10  # 目標の5分を超える

        updated_session = ProgressService.end_session(session, chords, duration_minutes)

        assert updated_session.goal_achieved is True

    def test_end_session_sets_goal_achieved_false_when_goal_not_met(
        self, django_user_model
    ):
        """end_sessionは目標未達時にgoal_achievedをFalseにする"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=10
        )

        session = ProgressService.start_session(user)
        chords = ["C"]
        duration_minutes = 5  # 目標の10分に満たない

        updated_session = ProgressService.end_session(session, chords, duration_minutes)

        assert updated_session.goal_achieved is False

    def test_end_session_handles_empty_chords_list(self, django_user_model):
        """end_sessionは空のコードリストを処理できる"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        session = ProgressService.start_session(user)
        chords = []
        duration_minutes = 5

        updated_session = ProgressService.end_session(session, chords, duration_minutes)

        assert updated_session.chords_practiced == []
        assert updated_session.duration_minutes == 5

    def test_end_session_updates_last_practice_date(self, django_user_model):
        """end_sessionは最終練習日を更新する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        session = ProgressService.start_session(user)
        chords = ["C"]
        duration_minutes = 5

        ProgressService.end_session(session, chords, duration_minutes)

        user.refresh_from_db()
        today = timezone.now().date()
        assert user.last_practice_date == today

    def test_get_monthly_stats_returns_30_days_of_data(self, django_user_model):
        """get_monthly_statsは30日間の統計データを返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 過去30日間の統計を取得
        stats = ProgressService.get_monthly_stats(user, days=30)

        # 30日分のデータが返されることを確認
        assert len(stats) == 30
        assert all("date" in stat and "minutes" in stat for stat in stats)

    def test_get_monthly_stats_includes_practice_data(self, django_user_model):
        """get_monthly_statsは練習データを含む"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 今日のセッションを作成
        session = ProgressService.start_session(user)
        ProgressService.end_session(session, ["C", "G"], 30)

        # 統計を取得
        stats = ProgressService.get_monthly_stats(user, days=30)

        # 今日のデータに30分が含まれていることを確認
        today = timezone.now().date()
        today_stat = next((s for s in stats if s["date"] == today.isoformat()), None)
        assert today_stat is not None
        assert today_stat["minutes"] == 30

    def test_get_monthly_stats_fills_missing_days_with_zero(self, django_user_model):
        """get_monthly_statsはデータがない日を0で埋める"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 統計を取得
        stats = ProgressService.get_monthly_stats(user, days=30)

        # すべての日にデータがあることを確認
        assert len(stats) == 30
        # 練習がない日は0分であることを確認
        assert all(stat["minutes"] >= 0 for stat in stats)

    def test_get_monthly_stats_aggregates_multiple_sessions_per_day(
        self, django_user_model
    ):
        """get_monthly_statsは1日の複数セッションを集計する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 同日に複数のセッションを作成
        session1 = ProgressService.start_session(user)
        ProgressService.end_session(session1, ["C"], 15)

        session2 = ProgressService.start_session(user)
        ProgressService.end_session(session2, ["G"], 20)

        # 統計を取得
        stats = ProgressService.get_monthly_stats(user, days=30)

        # 今日の合計が35分であることを確認
        today = timezone.now().date()
        today_stat = next((s for s in stats if s["date"] == today.isoformat()), None)
        assert today_stat is not None
        assert today_stat["minutes"] == 35
