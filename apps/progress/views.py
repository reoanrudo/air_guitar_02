"""
Progress views for VirtuTune

進捗表示画面のビュー
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import logging
import json

from apps.progress.services import ProgressService
from apps.progress.models import PracticeSession

logger = logging.getLogger(__name__)


class ProgressView(LoginRequiredMixin, TemplateView):
    """
    進捗表示画面ビュー

    練習統計と進捗グラフを表示する
    """

    template_name = "progress/progress.html"

    def get_context_data(self, **kwargs):
        """
        テンプレートに渡すコンテキストデータを構築

        Returns:
            dict: 統計データを含むコンテキスト
        """
        context = super().get_context_data(**kwargs)

        # ユーザーを取得
        user = self.request.user

        try:
            # 日次統計を取得（過去7日間と30日間）
            daily_stats = ProgressService.get_daily_stats(user, days=7)
            monthly_stats = ProgressService.get_monthly_stats(user, days=30)

            # 総計統計を取得
            total_stats = ProgressService.get_total_stats(user)

            # 目標達成状況をチェック
            goal_status = ProgressService.check_goal_achievement(user)

            # 最近の練習セッションを取得（最新5件）
            recent_sessions = PracticeSession.objects.filter(
                user=user, ended_at__isnull=False
            ).order_by("-started_at")[:5]

            # プログレスバーのパーセンテージを計算
            if goal_status["goal_minutes"] > 0:
                progress_percentage = int(
                    (goal_status["today_minutes"] / goal_status["goal_minutes"]) * 100
                )
            else:
                progress_percentage = 100 if goal_status["today_minutes"] > 0 else 0

            # コンテキストに追加
            context.update(
                {
                    "daily_stats": daily_stats,
                    "monthly_stats": monthly_stats,
                    "total_stats": total_stats,
                    "goal_status": goal_status,
                    "progress_percentage": min(
                        progress_percentage, 100
                    ),  # 100%を超えないように
                    "recent_sessions": recent_sessions,
                    "daily_stats_json": json.dumps(daily_stats),
                    "monthly_stats_json": json.dumps(monthly_stats),
                    "total_stats_json": json.dumps(total_stats),
                }
            )

            logger.info(
                f"進捗表示データ取得成功: user_id={user.id}, "
                f"daily_stats_count={len(daily_stats)}, "
                f"goal_achieved={goal_status['achieved']}"
            )

        except Exception:
            logger.error(
                f"進捗表示データ取得失敗: user_id={user.id}",
                exc_info=True,
                extra={"user_id": user.id},
            )
            # エラー時は空のデータを設定
            context.update(
                {
                    "daily_stats": [],
                    "monthly_stats": [],
                    "total_stats": {
                        "total_minutes": 0,
                        "total_hours": 0,
                        "streak_days": 0,
                        "today_minutes": 0,
                        "goal_minutes": user.daily_goal_minutes,
                        "goal_achieved": False,
                    },
                    "goal_status": {
                        "achieved": False,
                        "today_minutes": 0,
                        "goal_minutes": user.daily_goal_minutes,
                        "remaining_minutes": user.daily_goal_minutes,
                    },
                    "progress_percentage": 0,
                    "recent_sessions": [],
                    "daily_stats_json": json.dumps([]),
                    "monthly_stats_json": json.dumps([]),
                    "total_stats_json": json.dumps(
                        {
                            "total_minutes": 0,
                            "total_hours": 0,
                            "streak_days": 0,
                            "today_minutes": 0,
                            "goal_minutes": user.daily_goal_minutes,
                            "goal_achieved": False,
                        }
                    ),
                }
            )

        return context


@login_required
@require_POST
def refresh_stats_api(request):
    """
    統計データを更新するAPIエンドポイント

    Ajaxで統計データを再取得する際に使用

    Returns:
        JsonResponse: 更新された統計データ
    """
    user = request.user

    try:
        # 統計を再取得
        daily_stats = ProgressService.get_daily_stats(user, days=7)
        monthly_stats = ProgressService.get_monthly_stats(user, days=30)
        total_stats = ProgressService.get_total_stats(user)

        return JsonResponse(
            {
                "success": True,
                "daily_stats": daily_stats,
                "monthly_stats": monthly_stats,
                "total_stats": total_stats,
            },
            status=200,
        )

    except Exception:
        logger.error(
            f"統計更新APIエラー: user_id={user.id}",
            exc_info=True,
            extra={"user_id": user.id},
        )
        return JsonResponse(
            {"success": False, "error": "統計データの取得に失敗しました"}, status=500
        )
