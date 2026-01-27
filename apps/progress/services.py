"""
Progress service for VirtuTune

練習セッションと進捗管理に関するビジネスロジック
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import DatabaseError, transaction
from django.db.models import Sum
from apps.progress.models import PracticeSession

logger = logging.getLogger(__name__)


class ProgressService:
    """
    練習進捗管理サービスクラス

    練習セッションの作成、終了、統計更新などの
    ビジネスロジックを提供する
    """

    @staticmethod
    def start_session(user) -> Optional[PracticeSession]:
        """
        新しい練習セッションを作成する

        Args:
            user: 練習を開始するユーザー

        Returns:
            作成された練習セッション。失敗時はNone

        Raises:
            DatabaseError: データベースエラーが発生した場合
        """
        try:
            session = PracticeSession.objects.create(
                user=user, started_at=timezone.now()
            )
            logger.info(
                f"練習セッション作成成功: user_id={user.id}, session_id={session.id}"
            )
            return session

        except DatabaseError:
            logger.error(
                f"練習セッション作成失敗: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            raise

    @staticmethod
    def end_session(
        session: PracticeSession, chords: List[str], duration_minutes: int
    ) -> Optional[PracticeSession]:
        """
        練習セッションを終了し、統計を更新する

        Args:
            session: 終了する練習セッション
            chords: 練習したコードのリスト
            duration_minutes: 練習時間（分）

        Returns:
            更新された練習セッション。失敗時はNone

        Raises:
            DatabaseError: データベースエラーが発生した場合
        """
        try:
            with transaction.atomic():
                # セッションを更新
                session.ended_at = timezone.now()
                session.duration_minutes = duration_minutes
                session.chords_practiced = chords

                # 目標達成判定
                if session.user.daily_goal_minutes > 0:
                    session.goal_achieved = (
                        duration_minutes >= session.user.daily_goal_minutes
                    )
                else:
                    session.goal_achieved = False

                session.save()

                # ユーザー統計を更新
                user = session.user
                user.total_practice_minutes += duration_minutes
                user.last_practice_date = timezone.now().date()
                user.save()

                logger.info(
                    f"練習セッション終了成功: "
                    f"session_id={session.id}, "
                    f"duration={duration_minutes}分, "
                    f"goal_achieved={session.goal_achieved}"
                )

                return session

        except DatabaseError:
            logger.error(
                f"練習セッション終了失敗: session_id={session.id}",
                exc_info=True,
                extra={"session_id": session.id},
            )
            raise

    @staticmethod
    def calculate_duration(started_at: datetime, ended_at: datetime) -> int:
        """
        練習時間を計算する（分単位）

        秒数は切り捨てて分単位で返す

        Args:
            started_at: 開始日時
            ended_at: 終了日時

        Returns:
            練習時間（分）

        Example:
            >>> started_at = datetime(2026, 1, 27, 10, 0, 0)
            >>> ended_at = datetime(2026, 1, 27, 10, 5, 30)
            >>> ProgressService.calculate_duration(started_at, ended_at)
            5
        """
        if ended_at < started_at:
            logger.warning(
                f"終了時刻が開始時刻より前です: "
                f"started={started_at}, ended={ended_at}"
            )
            return 0

        duration = ended_at - started_at
        duration_minutes = int(duration.total_seconds() // 60)

        return duration_minutes

    @staticmethod
    def get_daily_stats(user, days: int = 7) -> List[Dict[str, any]]:
        """
        過去N日間の練習時間を取得

        Args:
            user: 統計を取得するユーザー
            days: 取得する日数（デフォルト7日）

        Returns:
            日次統計のリスト [{"date": "2026-01-20", "minutes": 30}, ...]

        Example:
            >>> stats = ProgressService.get_daily_stats(user, days=7)
            >>> len(stats)
            7
        """
        try:
            # タイムゾーンを考慮して今日の日付を取得
            today = timezone.now().date()
            start_date = today - timedelta(days=days - 1)

            # 開始日から終了日までのセッションを取得
            sessions = (
                PracticeSession.objects.filter(
                    user=user,
                    started_at__date__gte=start_date,
                    started_at__date__lte=today,
                )
                .values("started_at__date")
                .annotate(total_minutes=Sum("duration_minutes"))
                .order_by("started_at__date")
            )

            # 日次統計を作成
            daily_stats = []
            for session in sessions:
                daily_stats.append(
                    {
                        "date": session["started_at__date"].isoformat(),
                        "minutes": session["total_minutes"] or 0,
                    }
                )

            logger.info(
                f"日次統計取得成功: user_id={user.id}, "
                f"days={days}, stats_count={len(daily_stats)}"
            )

            return daily_stats

        except DatabaseError:
            logger.error(
                f"日次統計取得失敗: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            return []

    @staticmethod
    def get_monthly_stats(user, days: int = 30) -> List[Dict[str, any]]:
        """
        過去N日間の練習時間を取得（月次統計用）

        Args:
            user: 統計を取得するユーザー
            days: 取得する日数（デフォルト30日）

        Returns:
            日次統計のリスト [{"date": "2026-01-20", "minutes": 30}, ...]

        Example:
            >>> stats = ProgressService.get_monthly_stats(user, days=30)
            >>> len(stats)
            30
        """
        try:
            # タイムゾーンを考慮して今日の日付を取得
            today = timezone.now().date()
            start_date = today - timedelta(days=days - 1)

            # 開始日から終了日までのセッションを取得
            sessions = (
                PracticeSession.objects.filter(
                    user=user,
                    started_at__date__gte=start_date,
                    started_at__date__lte=today,
                )
                .values("started_at__date")
                .annotate(total_minutes=Sum("duration_minutes"))
                .order_by("started_at__date")
            )

            # 日次統計を作成（データがない日は0分として埋める）
            daily_stats = []
            sessions_dict = {
                session["started_at__date"]: session["total_minutes"] or 0
                for session in sessions
            }

            for i in range(days):
                current_date = start_date + timedelta(days=i)
                daily_stats.append(
                    {
                        "date": current_date.isoformat(),
                        "minutes": sessions_dict.get(current_date, 0),
                    }
                )

            logger.info(
                f"月次統計取得成功: user_id={user.id}, "
                f"days={days}, stats_count={len(daily_stats)}"
            )

            return daily_stats

        except DatabaseError:
            logger.error(
                f"月次統計取得失敗: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            return []

    @staticmethod
    def get_total_stats(user) -> Dict[str, any]:
        """
        総練習時間、ストリーク等の統計を取得

        Args:
            user: 統計を取得するユーザー

        Returns:
            総計統計を含む辞書:
            {
                'total_minutes': 総練習時間（分）,
                'total_hours': 総練習時間（時間）,
                'streak_days': 連続練習日数,
                'today_minutes': 今日の練習時間（分）,
                'goal_minutes': 1日の目標（分）,
                'goal_achieved': 今日の目標達成フラグ
            }

        Example:
            >>> stats = ProgressService.get_total_stats(user)
            >>> stats['total_minutes'] >= 0
            True
        """
        try:
            # 今日の練習時間を取得
            today = timezone.now().date()
            today_sessions = PracticeSession.objects.filter(
                user=user, started_at__date=today
            ).aggregate(total_minutes=Sum("duration_minutes"))

            today_minutes = today_sessions["total_minutes"] or 0

            # 総練習時間と目標
            total_minutes = user.total_practice_minutes
            total_hours = round(total_minutes / 60, 1) if total_minutes > 0 else 0
            goal_minutes = user.daily_goal_minutes
            goal_achieved = today_minutes >= goal_minutes if goal_minutes > 0 else False

            # ストリークを計算
            streak_days = ProgressService.calculate_streak(user)

            stats = {
                "total_minutes": total_minutes,
                "total_hours": total_hours,
                "streak_days": streak_days,
                "today_minutes": today_minutes,
                "goal_minutes": goal_minutes,
                "goal_achieved": goal_achieved,
            }

            logger.info(
                f"総計統計取得成功: user_id={user.id}, "
                f"total_minutes={total_minutes}, streak={streak_days}"
            )

            return stats

        except DatabaseError:
            logger.error(
                f"総計統計取得失敗: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            return {
                "total_minutes": 0,
                "total_hours": 0,
                "streak_days": 0,
                "today_minutes": 0,
                "goal_minutes": user.daily_goal_minutes,
                "goal_achieved": False,
            }

    @staticmethod
    def calculate_streak(user) -> int:
        """
        連続練習日数を計算

        昨日以前から連続して練習している日数を計算する。
        今日練習している場合は今日も含める。

        Args:
            user: ストリークを計算するユーザー

        Returns:
            連続練習日数（練習がない場合は0）

        Example:
            >>> streak = ProgressService.calculate_streak(user)
            >>> streak >= 0
            True
        """
        try:
            # 今日の日付を取得
            today = timezone.now().date()

            # 練習セッションを日付順に取得（降順）
            sessions = PracticeSession.objects.filter(user=user).dates(
                "started_at", "day", order="DESC"
            )

            if not sessions:
                return 0

            # 最新の練習日を取得
            last_practice = sessions[0]

            # 最新の練習日が今日か昨日でない場合、ストリークはリセットされている
            if last_practice not in [today, today - timedelta(days=1)]:
                return 0

            # 連続日数をカウント
            streak = 0
            check_date = today

            for session_date in sessions:
                if session_date == check_date:
                    streak += 1
                    check_date -= timedelta(days=1)
                elif session_date < check_date:
                    # 連続が途切れた
                    break

            logger.info(f"ストリーク計算成功: user_id={user.id}, streak={streak}")

            return streak

        except DatabaseError:
            logger.error(
                f"ストリーク計算失敗: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            return 0

    @staticmethod
    def check_goal_achievement(user) -> Dict[str, int]:
        """
        目標達成状況をチェックする

        今日の練習時間を合計し、目標と比較して達成状況を返す

        Args:
            user: チェック対象のユーザー

        Returns:
            達成状況を含む辞書:
            {
                'achieved': bool,          # 目標達成フラグ
                'today_minutes': int,       # 今日の練習時間（分）
                'goal_minutes': int,        # 目標時間（分）
                'remaining_minutes': int    # 残り時間（分）
            }

        Example:
            >>> user = User.objects.get(pk=1)
            >>> result = ProgressService.check_goal_achievement(user)
            >>> print(result['achieved'], result['today_minutes'])
        """
        try:
            # 今日の日付を取得
            today = timezone.now().date()

            # 今日の完了した練習セッションを取得
            today_sessions = PracticeSession.objects.filter(
                user=user,
                started_at__date=today,
                ended_at__isnull=False,  # 完了したセッションのみ
            )

            # 今日の練習時間を合計
            today_minutes = sum(session.duration_minutes for session in today_sessions)

            # 目標時間を取得
            goal_minutes = user.daily_goal_minutes

            # 目標達成判定
            achieved = today_minutes >= goal_minutes if goal_minutes > 0 else True

            # 残り時間を計算
            remaining_minutes = max(0, goal_minutes - today_minutes)

            return {
                "achieved": achieved,
                "today_minutes": today_minutes,
                "goal_minutes": goal_minutes,
                "remaining_minutes": remaining_minutes,
            }

        except Exception:
            logger.error(
                f"目標達成チェックエラー: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            # エラー時は安全なデフォルト値を返す
            return {
                "achieved": False,
                "today_minutes": 0,
                "goal_minutes": user.daily_goal_minutes,
                "remaining_minutes": user.daily_goal_minutes,
            }
