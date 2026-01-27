"""
Progress views tests for VirtuTune

進捗表示画面のビューのテスト
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.test import Client
from django.urls import reverse
from apps.progress.models import PracticeSession


@pytest.mark.django_db
class TestProgressView:
    """ProgressViewのテスト"""

    def test_view_requires_login(self):
        """進捗表示画面はログインが必要"""
        client = Client()
        url = reverse("progress:progress")

        response = client.get(url)

        assert response.status_code == 302
        assert response.url.startswith("/users/login/")

    def test_view_renders_for_authenticated_user(self, django_user_model):
        """ログインユーザーは進捗表示画面を閲覧できる"""
        # ユーザーを作成してログイン
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client = Client()
        client.force_login(user)

        url = reverse("progress:progress")
        response = client.get(url)

        assert response.status_code == 200
        assert "progress/progress.html" in [t.name for t in response.templates]

    def test_view_includes_daily_stats_in_context(self, django_user_model):
        """ビューは日次統計をコンテキストに含む"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        # 過去7日間のセッションを作成
        today = timezone.now().date()
        for i in range(7):
            session_date = today - timedelta(days=i)
            session_datetime = timezone.make_aware(
                timezone.datetime.combine(session_date, timezone.datetime.min.time())
            ) + timedelta(hours=12)

            PracticeSession.objects.create(
                user=user,
                started_at=session_datetime,
                ended_at=session_datetime + timedelta(minutes=10 + i),
                duration_minutes=10 + i,
            )

        client = Client()
        client.force_login(user)

        url = reverse("progress:progress")
        response = client.get(url)

        assert response.status_code == 200
        assert "daily_stats" in response.context
        assert len(response.context["daily_stats"]) == 7
        assert "monthly_stats" in response.context
        assert len(response.context["monthly_stats"]) == 30

    def test_view_includes_total_stats_in_context(self, django_user_model):
        """ビューは総計統計をコンテキストに含む"""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
            daily_goal_minutes=10,
            total_practice_minutes=150,
        )

        # 今日のセッションを作成
        today = timezone.now().date()
        session_datetime = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )

        PracticeSession.objects.create(
            user=user,
            started_at=session_datetime,
            ended_at=session_datetime + timedelta(minutes=15),
            duration_minutes=15,
        )

        client = Client()
        client.force_login(user)

        url = reverse("progress:progress")
        response = client.get(url)

        assert response.status_code == 200
        assert "total_stats" in response.context
        assert response.context["total_stats"]["total_minutes"] == 150
        assert response.context["total_stats"]["total_hours"] == 2.5
        assert response.context["total_stats"]["today_minutes"] == 15
        assert response.context["total_stats"]["goal_achieved"] is True

    def test_view_handles_no_practice_sessions(self, django_user_model):
        """ビューは練習記録がない場合でも正常に動作する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        client = Client()
        client.force_login(user)

        url = reverse("progress:progress")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["daily_stats"] == []
        # monthly_statsは30日分のデータを返す（0分のデータも含む）
        assert len(response.context["monthly_stats"]) == 30
        assert all(stat["minutes"] == 0 for stat in response.context["monthly_stats"])
        assert response.context["total_stats"]["total_minutes"] == 0
        assert response.context["total_stats"]["streak_days"] == 0

    def test_view_shows_goal_achievement_status(self, django_user_model):
        """ビューは目標達成状況を表示する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=10
        )

        # 今日のセッション（目標未達成）
        today = timezone.now().date()
        session_datetime = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )

        PracticeSession.objects.create(
            user=user,
            started_at=session_datetime,
            ended_at=session_datetime + timedelta(minutes=5),
            duration_minutes=5,
        )

        client = Client()
        client.force_login(user)

        url = reverse("progress:progress")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["total_stats"]["goal_achieved"] is False
        assert response.context["total_stats"]["today_minutes"] == 5


@pytest.mark.django_db
class TestRefreshStatsAPI:
    """refresh_stats_apiのテスト"""

    def test_api_requires_login(self):
        """APIはログインが必要"""
        client = Client()
        url = reverse("progress:refresh_stats")

        response = client.post(url)

        assert response.status_code == 302
        assert response.url.startswith("/users/login/")

    def test_api_requires_post_method(self, django_user_model):
        """APIはPOSTメソッドのみ受け付ける"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client = Client()
        client.force_login(user)

        url = reverse("progress:refresh_stats")

        # GETは許可しない
        response = client.get(url)
        assert response.status_code == 405

    def test_api_returns_stats_data(self, django_user_model):
        """APIは統計データをJSONで返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", total_practice_minutes=100
        )

        client = Client()
        client.force_login(user)

        url = reverse("progress:refresh_stats")
        response = client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "daily_stats" in data
        assert "monthly_stats" in data
        assert "total_stats" in data
        assert data["total_stats"]["total_minutes"] == 100

    def test_api_handles_errors_gracefully(self, django_user_model):
        """APIはエラーを適切に処理する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )

        client = Client()
        client.force_login(user)

        url = reverse("progress:refresh_stats")
        response = client.post(url)

        # エラーがなく、成功レスポンスを返す
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
