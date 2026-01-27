"""
Services for ranking app

ランキング機能のサービス層
"""

import random
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from datetime import timedelta
from typing import Optional, List

from apps.game.models import Song, Score, Achievement, UserAchievement
from apps.progress.models import PracticeSession

User = get_user_model()

logger = logging.getLogger(__name__)


class RankingService:
    """ランキングサービス

    ランキングに関するビジネスロジックを提供する
    """

    # ハンドルネーム生成用の形容詞と名詞
    ADJECTIVES = [
        "Happy",
        "Brave",
        "Swift",
        "Cool",
        "Mighty",
        "Silent",
        "Wild",
        "Lucky",
        "Epic",
        "Bold",
        "Bright",
        "Chill",
        "Groovy",
        "Jazzy",
        "Rock",
        "Soul",
        "Zen",
        "Funky",
        "Fresh",
        "Grand",
    ]

    NOUNS = [
        "Guitarist",
        "Player",
        "Master",
        "Hero",
        "Legend",
        "Star",
        "Rockstar",
        "Virtuoso",
        "Maestro",
        "Artist",
        "Strummer",
        "Performer",
        "Musician",
        "Soloist",
        "Bard",
        "Troubadour",
        "Minstrel",
        "Melodist",
        "Rhythm",
        "Jammer",
    ]

    @staticmethod
    def get_daily_leaderboard(
        song_id: Optional[int] = None, limit: int = 100
    ) -> list[dict]:
        """
        日次ランキングを取得する

        Args:
            song_id: 楽曲ID（Noneの場合は全楽曲）
            limit: 取得件数

        Returns:
            ランキングリスト（順位、ユーザーID、ハンドルネーム、
            スコアを含む辞書のリスト）
        """
        today = timezone.now().date()

        # クエリ構築
        queryset = Score.objects.filter(date=today)

        if song_id is not None:
            queryset = queryset.filter(song_id=song_id)

        # スコアの高い順に取得
        scores = queryset.select_related("user", "song").order_by("-score")[:limit]

        # 結果を構築
        leaderboard = []
        for rank, score in enumerate(scores, start=1):
            handle_name = RankingService.generate_handle_name(score.user)

            leaderboard.append(
                {
                    "rank": rank,
                    "user_id": score.user_id,
                    "handle_name": handle_name,
                    "score": score.score,
                    "song_id": score.song_id,
                    "song_name": score.song.name,
                    "date": score.date,
                }
            )

        return leaderboard

    @staticmethod
    def get_weekly_leaderboard(
        song_id: Optional[int] = None, limit: int = 100
    ) -> list[dict]:
        """
        週間ランキングを取得する

        Args:
            song_id: 楽曲ID（Noneの場合は全楽曲）
            limit: 取得件数

        Returns:
            ランキングリスト（順位、ユーザーID、ハンドルネーム、
            スコアを含む辞書のリスト）
        """
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # クエリ構築（過去7日間）
        queryset = Score.objects.filter(date__gte=week_ago, date__lte=today)

        if song_id is not None:
            queryset = queryset.filter(song_id=song_id)

        # スコアの高い順に取得（各ユーザーの最高スコアを使用）
        scores = (
            queryset.values("user_id", "song_id")
            .annotate(max_score=models.Max("score"))
            .order_by("-max_score")[:limit]
        )

        # 結果を構築
        leaderboard = []
        for rank, entry in enumerate(scores, start=1):
            user = User.objects.get(id=entry["user_id"])
            song = Song.objects.get(id=entry["song_id"])
            handle_name = RankingService.generate_handle_name(user)

            leaderboard.append(
                {
                    "rank": rank,
                    "user_id": entry["user_id"],
                    "handle_name": handle_name,
                    "score": entry["max_score"],
                    "song_id": entry["song_id"],
                    "song_name": song.name,
                }
            )

        return leaderboard

    @staticmethod
    def generate_handle_name(user: User) -> str:
        """
        ユーザーのハンドルネームを生成する

        同じユーザーに対しては常に同じハンドルネームを生成する。
        ユーザーIDをシードに使用することで再現性を確保する。

        Args:
            user: ユーザーオブジェクト

        Returns:
            生成されたハンドルネーム（例: "HappyGuitarist123"）
        """
        # ユーザーIDをシードとして使用して、常に同じ組み合わせを生成
        random.seed(user.id)

        adjective = random.choice(RankingService.ADJECTIVES)
        noun = random.choice(RankingService.NOUNS)
        number = user.id % 1000  # ユーザーIDの下3桁

        # ランダムシードをリセット（セキュリティ上の理由）
        random.seed()

        return f"{adjective}{noun}{number:03d}"

    @staticmethod
    def get_user_rank(user: User, song_id: int, period: str = "daily") -> Optional[int]:
        """
        ユーザーの順位を取得する

        Args:
            user: ユーザーオブジェクト
            song_id: 楽曲ID
            period: 期間（"daily" または "weekly"）

        Returns:
            ユーザーの順位（スコアがない場合はNone）
        """
        if period == "daily":
            leaderboard = RankingService.get_daily_leaderboard(song_id=song_id)
        elif period == "weekly":
            leaderboard = RankingService.get_weekly_leaderboard(song_id=song_id)
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'daily' or 'weekly'.")

        # ユーザーの順位を検索
        for entry in leaderboard:
            if entry["user_id"] == user.id:
                return entry["rank"]

        return None

    @staticmethod
    def update_score(user: User, song: Song, score: int) -> Score:
        """
        スコアを更新する

        同じ日・同じ楽曲の場合は、最高スコアのみを保持する。

        Args:
            user: ユーザーオブジェクト
            song: 楽曲オブジェクト
            score: スコア

        Returns:
            更新されたスコアオブジェクト
        """
        today = timezone.now().date()

        # 既存のスコアを取得
        existing_score = Score.objects.filter(user=user, song=song, date=today).first()

        if existing_score:
            # 最高スコアのみを保持
            if score > existing_score.score:
                existing_score.score = score
                existing_score.save()
            return existing_score
        else:
            # 新規スコアを作成
            return Score.objects.create(user=user, song=song, score=score, date=today)


class AchievementUnlockService:
    """実績解除サービス

    実績の解除と管理を行う
    """

    @staticmethod  # noqa: C901
    def check_achievements(
        user: User, game_session, practice_session: Optional[PracticeSession]
    ) -> List[Achievement]:
        """
        実績をチェックして解除する

        Args:
            user: ユーザーオブジェクト
            game_session: ゲームセッションオブジェクト
            practice_session: 練習セッションオブジェクト（任意）

        Returns:
            新しく解除された実績のリスト
        """
        unlocked_achievements = []
        unlocked_achievements = []

        try:
            # 1. 初回プレイ実績
            if AchievementUnlockService._check_first_play(user):
                achievement = AchievementUnlockService.unlock_achievement(
                    user, "FIRST_PLAY"
                )
                if achievement:
                    unlocked_achievements.append(achievement)

            # 2. パーフェクトプレイ実績
            if game_session and AchievementUnlockService._check_perfect_play(
                game_session
            ):
                achievement = AchievementUnlockService.unlock_achievement(
                    user, "PERFECT_PLAY"
                )
                if achievement:
                    unlocked_achievements.append(achievement)

            # 3. ストリーク実績
            if AchievementUnlockService._check_streak_7(user):
                achievement = AchievementUnlockService.unlock_achievement(
                    user, "STREAK_7"
                )
                if achievement:
                    unlocked_achievements.append(achievement)

            # 4. スコア実績
            if game_session and AchievementUnlockService._check_score_1000(
                game_session
            ):
                achievement = AchievementUnlockService.unlock_achievement(
                    user, "SCORE_1000"
                )
                if achievement:
                    unlocked_achievements.append(achievement)

            # 5. コンボマスター実績
            if game_session and AchievementUnlockService._check_combo_master(
                game_session
            ):
                achievement = AchievementUnlockService.unlock_achievement(
                    user, "COMBO_MASTER"
                )
                if achievement:
                    unlocked_achievements.append(achievement)

            # 6. 練習時間実績
            if AchievementUnlockService._check_practice_hour(user):
                achievement = AchievementUnlockService.unlock_achievement(
                    user, "PRACTICE_HOUR"
                )
                if achievement:
                    unlocked_achievements.append(achievement)

        except Exception as e:
            logger.error(
                f"実績チェック中にエラーが発生しました: user_id={user.id}, error={e}",
                exc_info=True,
            )

        return unlocked_achievements

    @staticmethod
    def _check_first_play(user: User) -> bool:
        """初回プレイ実績のチェック"""
        # ユーザーのゲームセッション数を確認
        from apps.game.models import GameSession

        session_count = GameSession.objects.filter(user=user).count() if user.id else 0
        return session_count == 1

    @staticmethod
    def _check_perfect_play(game_session) -> bool:
        """パーフェクトプレイ実績のチェック"""
        return game_session and game_session.accuracy >= 1.0

    @staticmethod
    def _check_streak_7(user: User) -> bool:
        """7日連続練習実績のチェック"""
        return user.streak_days >= 7

    @staticmethod
    def _check_score_1000(game_session) -> bool:
        """スコア1000実績のチェック"""
        return game_session and game_session.score >= 1000

    @staticmethod
    def _check_combo_master(game_session) -> bool:
        """コンボマスター実績のチェック"""
        return game_session and game_session.max_combo >= 50

    @staticmethod
    def _check_practice_hour(user: User) -> bool:
        """練習時間実績のチェック"""
        return user.total_practice_minutes >= 60

    @staticmethod
    def unlock_achievement(user: User, achievement_name: str) -> Optional[Achievement]:
        """
        実績を解除する

        Args:
            user: ユーザーオブジェクト
            achievement_name: 実績名

        Returns:
            解除された実績オブジェクト（既に解除済みや失敗の場合はNone）
        """
        try:
            # 実績を取得
            achievement = Achievement.objects.get(name=achievement_name)

            # 既に解除済みか確認
            if UserAchievement.objects.filter(
                user=user, achievement=achievement
            ).exists():
                return None

            # 実績を解除
            UserAchievement.objects.create(user=user, achievement=achievement)

            logger.info(f"実績解除: user_id={user.id}, achievement={achievement_name}")

            return achievement

        except Achievement.DoesNotExist:
            logger.warning(f"実績が見つかりません: {achievement_name}")
            return None
        except Exception as e:
            logger.error(
                f"実績解除中にエラーが発生しました: user_id={user.id}, "
                f"achievement={achievement_name}, error={e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_user_achievements(user: User) -> List[UserAchievement]:
        """
        ユーザーの実績を取得する

        Args:
            user: ユーザーオブジェクト

        Returns:
            ユーザー実績のリスト（解除日時の降順）
        """
        return list(
            UserAchievement.objects.filter(user=user)
            .select_related("achievement")
            .order_by("-unlocked_at")
        )

    @staticmethod
    def get_achievement_progress(user: User) -> dict:
        """
        実績進捗を取得する

        Args:
            user: ユーザーオブジェクト

        Returns:
            進捗情報を含む辞書（total, unlocked, percentage）
        """
        total = Achievement.objects.count()
        unlocked = UserAchievement.objects.filter(user=user).count()
        percentage = (unlocked / total * 100) if total > 0 else 0

        return {
            "total": total,
            "unlocked": unlocked,
            "percentage": round(percentage, 2),
        }
