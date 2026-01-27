"""
ビュー: ゲーム機能

リズムゲームモードのビューを提供する
"""

import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from .models import Song, GameSession

logger = logging.getLogger(__name__)


class GameListView(LoginRequiredMixin, TemplateView):
    """
    ゲーム一覧ビュー

    利用可能な楽曲の一覧を表示する
    """

    template_name = "game/game_list.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        Returns:
            dict: 楽曲リストを含むコンテキスト
        """
        context = super().get_context_data(**kwargs)

        # 難易度順に楽曲を取得
        songs = Song.objects.all().order_by("difficulty", "display_order", "name")

        # 難易度グループに分類
        songs_by_difficulty = {}
        for song in songs:
            difficulty = song.difficulty
            if difficulty not in songs_by_difficulty:
                songs_by_difficulty[difficulty] = []
            songs_by_difficulty[difficulty].append(song)

        context["songs"] = songs
        context["songs_by_difficulty"] = songs_by_difficulty

        # ユーザーの最高スコアを取得
        if self.request.user.is_authenticated:
            user_best_scores = {}
            for session in GameSession.objects.filter(user=self.request.user).order_by(
                "-score"
            ):
                song_id = session.song_id
                if song_id not in user_best_scores:
                    user_best_scores[song_id] = session.score

            context["user_scores"] = user_best_scores

        return context


class GamePlayView(LoginRequiredMixin, TemplateView):
    """
    ゲームプレイビュー

    リズムゲームのプレイ画面を表示する
    """

    template_name = "game/game_play.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        Returns:
            dict: 楽曲データを含むコンテキスト
        """
        context = super().get_context_data(**kwargs)
        song_id = kwargs.get("song_id")

        # 楽曲データを取得
        song = get_object_or_404(Song, id=song_id)
        context["song"] = song

        # ノートデータをJSON形式で渡す
        context["notes_json"] = json.dumps(song.notes)

        return context


class GameResultView(LoginRequiredMixin, TemplateView):
    """
    ゲーム結果ビュー

    プレイ結果の統計情報を表示する
    """

    template_name = "game/game_result.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        Returns:
            dict: ゲームセッションデータを含むコンテキスト
        """
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get("session_id")

        # セッションデータを取得
        session = get_object_or_404(GameSession, id=session_id)

        # アクセス制御: 自分のセッションのみ表示可能
        if session.user != self.request.user:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("他ユーザーのゲーム結果は閲覧できません")

        context["session"] = session
        context["song"] = session.song

        # ランキング順位を計算
        rank = (
            GameSession.objects.filter(
                song=session.song, score__gt=session.score
            ).count()
            + 1
        )

        context["rank"] = rank

        # 評価を計算
        if session.accuracy >= 0.95:
            evaluation = "S"
        elif session.accuracy >= 0.90:
            evaluation = "A"
        elif session.accuracy >= 0.80:
            evaluation = "B"
        elif session.accuracy >= 0.70:
            evaluation = "C"
        else:
            evaluation = "D"

        context["evaluation"] = evaluation

        return context


@require_POST
def save_game_result(request):
    """
    ゲーム結果を保存する

    Args:
        request: HTTPリクエストオブジェクト

    Returns:
        JsonResponse: 保存結果
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "ログインが必要です"}, status=302)

    try:
        # POSTデータを解析
        data = json.loads(request.body)

        song_id = data.get("song_id")
        score = int(data.get("score", 0))
        max_combo = int(data.get("max_combo", 0))
        perfect_count = int(data.get("perfect_count", 0))
        great_count = int(data.get("great_count", 0))
        good_count = int(data.get("good_count", 0))
        miss_count = int(data.get("miss_count", 0))
        accuracy = float(data.get("accuracy", 0.0))

        # バリデーション
        if not song_id:
            return JsonResponse({"error": "song_idは必須です"}, status=400)

        if score < 0 or max_combo < 0:
            return JsonResponse(
                {"error": "スコアとコンボは0以上である必要があります"}, status=400
            )

        if not (0.0 <= accuracy <= 100.0):
            return JsonResponse(
                {"error": "精度は0〜100の範囲である必要があります"}, status=400
            )

        # 楽曲を取得
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return JsonResponse({"error": "楽曲が見つかりません"}, status=404)

        # ゲームセッションを作成
        session = GameSession.objects.create(
            user=request.user,
            song=song,
            score=score,
            max_combo=max_combo,
            perfect_count=perfect_count,
            great_count=great_count,
            good_count=good_count,
            miss_count=miss_count,
            accuracy=accuracy / 100.0,  # パーセントから小数に変換
        )

        # 実績チェック
        from apps.ranking.services import AchievementUnlockService

        unlocked_achievements = AchievementUnlockService.check_achievements(
            request.user, session, None
        )

        # 解除された実績の情報を準備
        new_achievements = [
            {
                "name": achievement.name,
                "description": achievement.description,
                "icon_url": achievement.icon_url,
                "tier": achievement.tier,
            }
            for achievement in unlocked_achievements
        ]

        logger.info(
            f"ゲーム結果を保存: user_id={request.user.id}, "
            f"song_id={song_id}, score={score}, accuracy={accuracy}, "
            f"unlocked_achievements={len(unlocked_achievements)}"
        )

        return JsonResponse(
            {
                "success": True,
                "session_id": session.id,
                "score": score,
                "accuracy": accuracy,
                "unlocked_achievements": new_achievements,
            },
            status=201,
        )

    except json.JSONDecodeError:
        logger.error("無効なJSONデータを受信")
        return JsonResponse({"error": "無効なJSONデータです"}, status=400)

    except ValueError:
        logger.error("データ型エラー")
        return JsonResponse({"error": "データ型が正しくありません"}, status=400)

    except Exception:
        logger.error(f"ゲーム結果保存エラー: user_id={request.user.id}", exc_info=True)
        return JsonResponse({"error": "サーバーエラーが発生しました"}, status=500)
