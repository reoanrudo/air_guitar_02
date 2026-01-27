"""
Guitar views for VirtuTune

仮想ギター画面のビュー
"""

import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import DatabaseError
from apps.guitar.models import Chord
from apps.progress.services import ProgressService
from apps.progress.models import PracticeSession

logger = logging.getLogger(__name__)


class GuitarView(LoginRequiredMixin, TemplateView):
    """
    仮想ギター画面ビュー

    ログインユーザーのみアクセス可能で、
    コードデータをテンプレートに渡す
    """

    template_name = "guitar/guitar.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        Returns:
            dict: コードデータを含むコンテキスト
        """
        context = super().get_context_data(**kwargs)
        context["chords"] = Chord.objects.all()
        return context


@login_required
@require_POST
def start_practice(request):
    """
    練習セッション開始API

    POST /guitar/api/start/

    リクエストボディ: なし

    レスポンス:
        {
            "session_id": int,
            "started_at": str (ISO 8601 format)
        }

    エラー:
        401: 未ログイン
        500: サーバーエラー
    """
    try:
        # 新しい練習セッションを作成
        session = ProgressService.start_session(request.user)

        # レスポンスデータを作成
        response_data = {
            "session_id": session.id,
            "started_at": session.started_at.isoformat(),
        }

        logger.info(f"練習開始: user_id={request.user.id}, session_id={session.id}")

        return JsonResponse(response_data, status=201)

    except DatabaseError:
        logger.error(
            f"練習開始失敗: user_id={request.user.id}",
            exc_info=True,
            extra={"user_id": request.user.id},
        )
        return JsonResponse({"error": "データベースエラーが発生しました"}, status=500)

    except Exception:
        logger.error(
            f"練習開始中の予期しないエラー: user_id={request.user.id}",
            exc_info=True,
            extra={"user_id": request.user.id},
        )
        return JsonResponse({"error": "サーバーエラーが発生しました"}, status=500)


@login_required
@require_POST
def end_practice(request):
    """
    練習セッション終了API

    POST /guitar/api/end/

    リクエストボディ:
        {
            "session_id": int,
            "chords": [str, str, ...]
        }

    レスポンス:
        {
            "success": true,
            "session_id": int,
            "duration_minutes": int,
            "goal_achieved": bool
        }

    エラー:
        400: 不正なリクエスト（無効なsession_id、不正なJSON）
        401: 未ログイン
        500: サーバーエラー
    """
    try:
        # リクエストボディをパース
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "不正なJSON形式です"}, status=400)

        # 必須パラメータのバリデーション
        session_id = data.get("session_id")
        if not session_id:
            return JsonResponse({"error": "session_idは必須です"}, status=400)

        chords = data.get("chords", [])
        if not isinstance(chords, list):
            return JsonResponse(
                {"error": "chordsは配列である必要があります"}, status=400
            )

        # セッションの存在確認
        try:
            session = PracticeSession.objects.get(id=session_id, user=request.user)
        except PracticeSession.DoesNotExist:
            return JsonResponse({"error": "無効なセッションIDです"}, status=400)

        # 練習時間を計算
        duration_minutes = ProgressService.calculate_duration(
            session.started_at, timezone.now()
        )

        # セッションを終了
        updated_session = ProgressService.end_session(session, chords, duration_minutes)

        # レスポンスデータを作成
        response_data = {
            "success": True,
            "session_id": updated_session.id,
            "duration_minutes": duration_minutes,
            "goal_achieved": updated_session.goal_achieved,
        }

        logger.info(
            f"練習終了: user_id={request.user.id}, "
            f"session_id={session.id}, duration={duration_minutes}分"
        )

        return JsonResponse(response_data, status=200)

    except DatabaseError:
        logger.error(
            f"練習終了失敗: user_id={request.user.id}",
            exc_info=True,
            extra={"user_id": request.user.id},
        )
        return JsonResponse({"error": "データベースエラーが発生しました"}, status=500)

    except Exception:
        logger.error(
            f"練習終了中の予期しないエラー: user_id={request.user.id}",
            exc_info=True,
            extra={"user_id": request.user.id},
        )
        return JsonResponse({"error": "サーバーエラーが発生しました"}, status=500)
