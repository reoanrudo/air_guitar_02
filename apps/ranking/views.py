"""
Views for ranking app

ランキング機能のビュー層
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse

from apps.game.models import Song, Achievement
from apps.ranking.services import RankingService, AchievementUnlockService


class RankingView(LoginRequiredMixin, TemplateView):
    """
    ランキングページのビュー

    日次・週間ランキングを表示する
    """

    template_name = "ranking/ranking.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        Returns:
            テンプレートに渡すコンテキスト
        """
        context = super().get_context_data(**kwargs)

        # 全楽曲を取得
        songs = Song.objects.all().order_by("display_order", "name")
        context["songs"] = songs

        # デフォルトで最初の楽曲を選択
        selected_song_id = self.request.GET.get("song_id")
        if selected_song_id:
            try:
                selected_song_id = int(selected_song_id)
            except (ValueError, TypeError):
                selected_song_id = songs.first().id if songs.exists() else None
        else:
            selected_song_id = songs.first().id if songs.exists() else None

        context["selected_song_id"] = selected_song_id

        # 日次ランキングを取得
        if selected_song_id:
            daily_leaderboard = RankingService.get_daily_leaderboard(
                song_id=selected_song_id, limit=100
            )
            weekly_leaderboard = RankingService.get_weekly_leaderboard(
                song_id=selected_song_id, limit=100
            )

            # 現在のユーザーの順位を取得
            user_daily_rank = RankingService.get_user_rank(
                user=self.request.user, song_id=selected_song_id, period="daily"
            )
            user_weekly_rank = RankingService.get_user_rank(
                user=self.request.user, song_id=selected_song_id, period="weekly"
            )

            context["daily_leaderboard"] = daily_leaderboard
            context["weekly_leaderboard"] = weekly_leaderboard
            context["user_daily_rank"] = user_daily_rank
            context["user_weekly_rank"] = user_weekly_rank

        return context


def api_daily_leaderboard(request):
    """
    日次ランキングAPI

    Args:
        request: HTTPリクエスト

    Returns:
        JSON形式のランキングデータ
    """
    song_id = request.GET.get("song_id")

    if not song_id:
        return JsonResponse({"error": "song_id is required"}, status=400)

    try:
        song_id = int(song_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid song_id"}, status=400)

    leaderboard = RankingService.get_daily_leaderboard(song_id=song_id, limit=100)

    return JsonResponse({"leaderboard": leaderboard})


def api_weekly_leaderboard(request):
    """
    週間ランキングAPI

    Args:
        request: HTTPリクエスト

    Returns:
        JSON形式のランキングデータ
    """
    song_id = request.GET.get("song_id")

    if not song_id:
        return JsonResponse({"error": "song_id is required"}, status=400)

    try:
        song_id = int(song_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid song_id"}, status=400)

    leaderboard = RankingService.get_weekly_leaderboard(song_id=song_id, limit=100)

    return JsonResponse({"leaderboard": leaderboard})


class AchievementView(LoginRequiredMixin, TemplateView):
    """
    実績ページのビュー

    ユーザーの実績一覧を表示する
    """

    template_name = "ranking/achievements.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        Returns:
            テンプレートに渡すコンテキスト
        """
        context = super().get_context_data(**kwargs)

        # ユーザーの実績を取得
        user_achievements = AchievementUnlockService.get_user_achievements(
            self.request.user
        )

        # 実績進捗を取得
        progress = AchievementUnlockService.get_achievement_progress(self.request.user)

        # 未解除の実績を取得
        unlocked_ids = [ua.achievement_id for ua in user_achievements]
        locked_achievements = Achievement.objects.exclude(id__in=unlocked_ids).order_by(
            "display_order", "tier", "name"
        )

        context["user_achievements"] = user_achievements
        context["locked_achievements"] = locked_achievements
        context["progress"] = progress

        return context
