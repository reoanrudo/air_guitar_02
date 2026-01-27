"""
Tests for Reminder Service

リマインダー機能のテスト
"""

from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from django.template.loader import render_to_string
from django.test import override_settings
from django.utils import timezone

from apps.progress.models import PracticeSession
from apps.reminders.services import (
    check_missed_practices,
    get_users_for_reminder,
    send_daily_reminders,
)
from apps.users.models import User


@pytest.mark.django_db
class TestReminderService:
    """ReminderServiceのテストクラス"""

    @pytest.fixture
    def user_with_reminder(self, db):
        """リマインダー有効なテストユーザーを作成"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            reminder_enabled=True,
            reminder_time=time(9, 0),  # 9:00 AM
            daily_goal_minutes=5,
            streak_days=7,
        )
        return user

    @pytest.fixture
    def user_without_reminder(self, db):
        """リマインダー無効なテストユーザーを作成"""
        user = User.objects.create_user(
            username="noreminduser",
            email="noremind@example.com",
            password="testpass123",
            reminder_enabled=False,
            daily_goal_minutes=5,
            streak_days=3,
        )
        return user

    @pytest.fixture
    def user_with_streak(self, db):
        """ストリークがあるユーザーを作成"""
        user = User.objects.create_user(
            username="streakuser",
            email="streak@example.com",
            password="testpass123",
            reminder_enabled=True,
            daily_goal_minutes=5,
            streak_days=14,
        )
        return user

    def test_send_daily_reminders_to_user_who_hasnt_practiced(self, user_with_reminder):
        """今日まだ練習していないユーザーにリマインダーを送信するテスト"""
        # 現在時刻を9:00 AMに設定
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 9, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch("apps.reminders.services.send_mail") as mock_mail:
                result = send_daily_reminders()

                # メール送信が1回呼ばれたことを確認
                assert mock_mail.called
                assert result["sent_count"] == 1
                assert result["total_users"] >= 1

    def test_send_daily_reminders_skips_user_who_practiced_today(
        self, user_with_reminder
    ):
        """今日既に練習したユーザーにはリマインダーを送信しないテスト"""
        # 今日の練習セッションを作成
        PracticeSession.objects.create(
            user=user_with_reminder,
            started_at=timezone.now(),
            duration_minutes=10,
        )

        # 現在時刻を9:00 AMに設定
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 9, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch("apps.reminders.services.send_mail"):
                result = send_daily_reminders()

                # メールが送信されていないことを確認
                assert result["sent_count"] == 0

    def test_send_daily_reminders_respects_time_window(self, user_with_reminder):
        """リマインダー時刻の±1時間以内のみ送信するテスト"""
        # 現在時刻を11:00 AMに設定（9:00から2時間後）
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 11, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch("apps.reminders.services.send_mail"):
                result = send_daily_reminders()

                # 時刻ウィンドウ外なのでメール送信されない
                assert result["sent_count"] == 0
                assert result["skipped_count"] >= 1

    def test_check_missed_practices_sends_warning_to_users_with_streak(
        self, user_with_streak
    ):
        """ストリークがあり、昨日練習していないユーザーに警告を送信するテスト"""
        # 昨日の練習記録を作成（一昨日まで練習していた）
        yesterday = timezone.now().date() - timedelta(days=2)
        PracticeSession.objects.create(
            user=user_with_streak,
            started_at=timezone.make_aware(
                datetime.combine(yesterday, time(10, 0)),
                timezone.get_current_timezone(),
            ),
            duration_minutes=10,
        )

        # 現在時刻を設定
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 10, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch("apps.reminders.services.send_mail") as mock_mail:
                result = check_missed_practices()

                # メール送信が1回呼ばれたことを確認
                assert mock_mail.called
                assert result["sent_count"] == 1
                assert result["total_missed"] >= 1

    def test_check_missed_practices_skips_users_who_practiced_yesterday(
        self, user_with_streak
    ):
        """昨日練習したユーザーには警告を送信しないテスト"""
        # 昨日の練習記録を作成
        yesterday = timezone.now().date() - timedelta(days=1)
        PracticeSession.objects.create(
            user=user_with_streak,
            started_at=timezone.make_aware(
                datetime.combine(yesterday, time(10, 0)),
                timezone.get_current_timezone(),
            ),
            duration_minutes=10,
        )

        # 現在時刻を設定
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 10, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch("apps.reminders.services.send_mail"):
                result = check_missed_practices()

                # メールが送信されていないことを確認
                assert result["sent_count"] == 0
                assert result["total_missed"] == 0

    def test_check_missed_practices_only_warns_users_with_positive_streak(
        self, user_with_reminder, db
    ):
        """ストリークが0のユーザーには警告を送信しないテスト"""
        # ストリークを0に設定
        user_with_reminder.streak_days = 0
        user_with_reminder.save()

        # 現在時刻を設定
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 10, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch("apps.reminders.services.send_mail"):
                result = check_missed_practices()

                # メールが送信されていないことを確認
                assert result["sent_count"] == 0

    def test_get_users_for_reminder_returns_correct_users(self, user_with_reminder):
        """指定時刻にリマインダーを送信すべきユーザーを正しく取得するテスト"""
        target_time = time(9, 0)

        users = get_users_for_reminder(target_time)

        # リマインダー有効で、時刻が一致するユーザーが含まれている
        assert user_with_reminder in users

    def test_get_users_for_reminder_filters_by_time_window(
        self, user_with_reminder, db
    ):
        """時刻ウィンドウ（±1時間）でフィルタリングするテスト"""
        # ユーザーのリマインダー時刻を9:00に設定済み

        # 8:00（1時間前）は含まれる
        users = get_users_for_reminder(time(8, 0))
        assert user_with_reminder in users

        # 10:00（1時間後）は含まれる
        users = get_users_for_reminder(time(10, 0))
        assert user_with_reminder in users

        # 7:00（2時間前）は含まれない
        users = get_users_for_reminder(time(7, 0))
        assert user_with_reminder not in users

        # 11:00（2時間後）は含まれない
        users = get_users_for_reminder(time(11, 0))
        assert user_with_reminder not in users

    def test_send_daily_reminders_handles_email_send_error(self, user_with_reminder):
        """メール送信エラーを適切に処理するテスト"""
        mock_now = timezone.make_aware(
            datetime(2026, 1, 27, 9, 0, 0), timezone.get_current_timezone()
        )

        with patch("apps.reminders.services.timezone.now", return_value=mock_now):
            with patch(
                "apps.reminders.services.send_mail",
                side_effect=Exception("SMTP Error"),
            ):
                result = send_daily_reminders()

                # エラーが発生してもタスクが完了することを確認
                assert "skipped_count" in result
                assert result["sent_count"] == 0

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_email_templates_render_correctly(self, user_with_reminder):
        """メールテンプレートが正しくレンダリングされるテスト"""
        context = {
            "user": user_with_reminder,
            "daily_goal_minutes": user_with_reminder.daily_goal_minutes,
            "streak_days": user_with_reminder.streak_days,
        }

        # リマインダーメールテンプレート
        reminder_html = render_to_string("reminders/reminder_email.html", context)
        assert user_with_reminder.username in reminder_html
        assert str(user_with_reminder.daily_goal_minutes) in reminder_html
        assert str(user_with_reminder.streak_days) in reminder_html

        # ストリーク警告メールテンプレート
        warning_context = {
            "user": user_with_reminder,
            "streak_days": user_with_reminder.streak_days,
        }
        warning_html = render_to_string(
            "reminders/streak_warning_email.html", warning_context
        )
        assert user_with_reminder.username in warning_html
        assert str(user_with_reminder.streak_days) in warning_html
