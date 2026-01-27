"""
Reminder Service for VirtuTune

練習リマインダーを送信するCeleryタスク
"""

import logging
from datetime import time, timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from apps.progress.models import PracticeSession
from config.settings import DEFAULT_FROM_EMAIL

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.reminders.services.send_daily_reminders",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_daily_reminders(self):
    """
    練習リマインダーメールを送信する

    reminder_enabled=True のユーザーで、現在時刻が
    reminder_time と一致（±1時間以内）するユーザーに送信する

    Returns:
        dict: 送信結果のサマリー
    """
    from apps.users.models import User

    try:
        now = timezone.now()
        current_time = now.time()
        today = now.date()

        # 現在時刻の±1時間以内にリマインダー時刻が設定されているユーザーを取得
        users_to_remind = User.objects.filter(
            reminder_enabled=True,
            reminder_time__isnull=False,
        )

        sent_count = 0
        skipped_count = 0

        for user in users_to_remind:
            # ユーザーのリマインダー時刻を取得
            reminder_time = user.reminder_time

            # 時刻の差分を計算（分単位）
            time_diff_minutes = abs(
                (current_time.hour * 60 + current_time.minute)
                - (reminder_time.hour * 60 + reminder_time.minute)
            )

            # ±1時間以内であれば送信
            if time_diff_minutes <= 60:
                # 今日の練習記録を確認
                has_practiced_today = PracticeSession.objects.filter(
                    user=user, started_at__date=today
                ).exists()

                if not has_practiced_today:
                    try:
                        # メールコンテキストを作成
                        context = {
                            "user": user,
                            "daily_goal_minutes": user.daily_goal_minutes,
                            "streak_days": user.streak_days,
                        }

                        # HTMLメールを作成
                        html_message = render_to_string(
                            "reminders/reminder_email.html", context
                        )
                        plain_message = strip_tags(html_message)

                        # メール送信
                        send_mail(
                            subject="【VirtuTune】今日の練習をお忘れなく！",
                            message=plain_message,
                            from_email=DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            html_message=html_message,
                            fail_silently=False,
                        )

                        sent_count += 1
                        logger.info(
                            f"リマインダー送信成功: user_id={user.id}, "
                            f"email={user.email}"
                        )

                    except Exception as e:
                        logger.error(
                            f"リマインダー送信失敗: user_id={user.id}, "
                            f"email={user.email}, error={str(e)}"
                        )
                        # 失敗した場合はスキップして次のユーザーへ
                        skipped_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1

        result = {
            "timestamp": now.isoformat(),
            "sent_count": sent_count,
            "skipped_count": skipped_count,
            "total_users": users_to_remind.count(),
        }

        logger.info(f"リマインダータスク完了: {result}")
        return result

    except Exception as e:
        logger.error(f"リマインダータスクエラー: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    name="apps.reminders.services.check_missed_practices",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def check_missed_practices(self):
    """
    練習していないユーザーに警告メールを送信する

    前日練習していないユーザーで、ストリークが0より大きい場合に
    ストリークが途切れる警告を送信する

    Returns:
        dict: 送信結果のサマリー
    """
    from apps.users.models import User

    try:
        now = timezone.now()
        yesterday = now.date() - timedelta(days=1)

        # 前日練習していないユーザーを取得
        users_who_missed = []
        users_with_streak = User.objects.filter(streak_days__gt=0)

        for user in users_with_streak:
            # 前日の練習記録を確認
            practiced_yesterday = PracticeSession.objects.filter(
                user=user, started_at__date=yesterday
            ).exists()

            if not practiced_yesterday:
                users_who_missed.append(user)

        sent_count = 0
        skipped_count = 0

        for user in users_who_missed:
            try:
                # メールコンテキストを作成
                context = {
                    "user": user,
                    "streak_days": user.streak_days,
                }

                # HTMLメールを作成
                html_message = render_to_string(
                    "reminders/streak_warning_email.html", context
                )
                plain_message = strip_tags(html_message)

                # メール送信
                send_mail(
                    subject=f"【VirtuTune】{user.streak_days}日間のストリークが途切れます！",
                    message=plain_message,
                    from_email=DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                sent_count += 1
                logger.info(
                    f"ストリーク警告送信成功: user_id={user.id}, "
                    f"email={user.email}, streak={user.streak_days}"
                )

            except Exception as e:
                logger.error(
                    f"ストリーク警告送信失敗: user_id={user.id}, "
                    f"email={user.email}, error={str(e)}"
                )
                skipped_count += 1

        result = {
            "timestamp": now.isoformat(),
            "sent_count": sent_count,
            "skipped_count": skipped_count,
            "total_missed": len(users_who_missed),
        }

        logger.info(f"ストリーク警告タスク完了: {result}")
        return result

    except Exception as e:
        logger.error(f"ストリーク警告タスクエラー: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


def get_users_for_reminder(target_time: time) -> list:
    """
    指定時刻にリマインダーを送信すべきユーザーを取得する

    Args:
        target_time: リマインダー送信対象時刻

    Returns:
        list: リマインダー対象のユーザーリスト
    """
    from apps.users.models import User

    # 指定時刻の±1時間以内に設定されているユーザーを取得
    users = User.objects.filter(
        reminder_enabled=True, reminder_time__isnull=False
    ).all()

    target_users = []
    for user in users:
        time_diff_minutes = abs(
            (target_time.hour * 60 + target_time.minute)
            - (user.reminder_time.hour * 60 + user.reminder_time.minute)
        )
        if time_diff_minutes <= 60:
            target_users.append(user)

    return target_users
