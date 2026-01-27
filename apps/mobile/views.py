"""
Mobileアプリのビュー

スマートフォンコントローラーとQRコードペアリング機能を提供する
HTTPポーリング方式でリアルタイム通信を実現
"""

import io
import json
import logging
import uuid

import qrcode
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .services import pairing_manager

logger = logging.getLogger(__name__)


# インメモリストレージ（開発環境用）
# 本番環境ではRedisを使用
_state_storage = {}


def get_state(session_id: str) -> dict:
    """セッションの状態を取得"""
    return _state_storage.get(session_id, {})


def set_state(session_id: str, key: str, value: any):
    """セッションの状態を設定"""
    if session_id not in _state_storage:
        _state_storage[session_id] = {}
    _state_storage[session_id][key] = value


@login_required
def generate_qr_code(request: HttpRequest) -> HttpResponse:
    """
    QRコードを生成する

    Cloudflare TunnelのURLを使用して、インターネット経由でアクセス可能なQRコードを生成する。

    Args:
        request: HTTPリクエストオブジェクト

    Returns:
        QRコード画像（PNG形式）
    """
    try:
        # ユニークなセッションIDを生成
        session_id = str(uuid.uuid4())

        # セッションをRedisに保存
        pairing_manager.create_session(request.user.id, session_id)

        # 状態ストレージを初期化
        set_state(session_id, 'user_id', request.user.id)
        set_state(session_id, 'current_chord', None)
        set_state(session_id, 'is_practice', False)
        set_state(session_id, 'camera_frame', None)

        # セッションIDをログに記録
        logger.info(f"QRコード生成: user_id={request.user.id}, session_id={session_id}")

        # Cloudflare TunnelのURL
        tunnel_url = "https://yang-deborah-especially-luke.trycloudflare.com"
        controller_url = f"{tunnel_url}/mobile/controller/?session={session_id}"

        # ログにURLを記録
        logger.info(f"QRコードURL: {controller_url}")

        # QRコードを生成
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(controller_url)
        qr.make(fit=True)

        # 画像を作成
        img = qr.make_image(fill_color="black", back_color="white")

        # バッファに保存
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/png")

    except Exception:
        logger.error(
            f"QRコード生成エラー: user_id={request.user.id}",
            exc_info=True,
            extra={"user_id": request.user.id},
        )
        # エラー時は空のレスポンスを返す
        return HttpResponse(b"", content_type="image/png", status=500)


@login_required
def validate_session(request: HttpRequest) -> JsonResponse:
    """
    セッションIDを検証するAPI

    スマートフォンから送信されたセッションIDを検証し、
    ペアリング可能かどうかを返す。

    Args:
        request: HTTPリクエストオブジェクト（POSTパラメータにsession_idを含む）

    Returns:
        JSONレスポンス
        - 成功時: {"valid": true, "user_id": 123}
        - 失敗時: {"valid": false, "error": "error message"}
    """
    if request.method != "POST":
        return JsonResponse(
            {"valid": False, "error": "POSTメソッドのみ許可されています"}, status=405
        )

    session_id = request.POST.get("session_id") or request.GET.get("session_id")

    if not session_id:
        return JsonResponse(
            {"valid": False, "error": "セッションIDが提供されていません"}, status=400
        )

    try:
        # セッションを検証
        is_valid = pairing_manager.validate_session(session_id)

        if is_valid:
            session = pairing_manager.get_session(session_id)
            return JsonResponse(
                {"valid": True, "user_id": session["user_id"] if session else None}
            )
        else:
            return JsonResponse(
                {"valid": False, "error": "無効なセッションIDまたは期限切れ"},
                status=400,
            )

    except Exception:
        logger.error(
            f"セッション検証エラー: session_id={session_id}",
            exc_info=True,
            extra={"session_id": session_id},
        )
        return JsonResponse(
            {"valid": False, "error": "サーバーエラーが発生しました"}, status=500
        )


def controller_entry(request: HttpRequest) -> HttpResponse:
    """
    モバイルコントローラーのエントリーページ

    スマートフォン用のコントローラー画面を表示する。
    QRコードでペアリングした後、このページでギター操作が可能になる。

    Args:
        request: HTTPリクエストオブジェクト

    Returns:
        モバイルコントローラーページのレンダリング結果

    Note:
        - 認証は不要（QRコードスキャンで直接アクセスするため）
        - セッションIDはURLパラメータから取得
    """
    # URLパラメータからセッションIDを取得
    session_id = request.GET.get('session', '')

    context = {
        "session_id": session_id,
    }

    return render(request, "mobile/controller.html", context)


@login_required
def get_current_session(request: HttpRequest) -> JsonResponse:
    """
    現在アクティブなセッションIDを取得するAPI

    PC側で通信を確立するために使用する。
    ユーザーごとの最新の有効なセッションIDを返す。

    Args:
        request: HTTPリクエストオブジェクト

    Returns:
        JSONレスポンス
        - 成功時: {"session_id": "uuid-string"}
        - 失敗時: {"session_id": null}
    """
    try:
        # 最新の有効なセッションを取得
        session = pairing_manager.get_user_latest_session(request.user.id)

        if session:
            return JsonResponse({"session_id": session["session_id"]})
        else:
            # セッションがない場合はnullを返す
            return JsonResponse({"session_id": None})

    except Exception as e:
        logger.error(
            f"セッション取得エラー: user_id={request.user.id}",
            exc_info=True,
            extra={"user_id": request.user.id},
        )
        return JsonResponse({"session_id": None}, status=500)


@csrf_exempt
def mobile_poll(request: HttpRequest) -> JsonResponse:
    """
    モバイルコントローラー用ポーリングAPI

    スマートフォンが定期的にこのエンドポイントを呼び出して、
    PCの状態（現在のコード、練習状態など）を取得する。

    Args:
        request: HTTPリクエストオブジェクト

    Returns:
        JSONレスポンス
        {
            "current_chord": "C" | null,
            "is_practice": true | false,
            "camera_frame": "base64..." | null,
            "timestamp": 1234567890
        }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ許可されています"}, status=405)

    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')

        if not session_id:
            return JsonResponse({"error": "セッションIDが必要です"}, status=400)

        # セッションを検証
        if not pairing_manager.validate_session(session_id):
            return JsonResponse({"error": "無効なセッションID"}, status=400)

        # 現在の状態を取得
        state = get_state(session_id)

        response = {
            "current_chord": state.get('current_chord'),
            "is_practice": state.get('is_practice', False),
            "camera_frame": state.get('camera_frame'),
            "timestamp": state.get('timestamp', 0),
        }

        return JsonResponse(response)

    except json.JSONDecodeError:
        return JsonResponse({"error": "無効なJSON形式"}, status=400)
    except Exception as e:
        logger.error(f"ポーリングエラー: {e}", exc_info=True)
        return JsonResponse({"error": "サーバーエラー"}, status=500)


@csrf_exempt
def mobile_command(request: HttpRequest) -> JsonResponse:
    """
    モバイルコントローラーからのコマンド受信API

    スマートフォンからの操作（コード変更、練習開始/終了）を
    PCに通知するために使用する。

    Args:
        request: HTTPリクエストオブジェクト

    Returns:
        JSONレスポンス
        {"success": true, "message": "コマンドを受信しました"}
    """
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ許可されています"}, status=405)

    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        command = data.get('command')
        params = data.get('params', {})

        if not session_id or not command:
            return JsonResponse({"error": "セッションIDとコマンドが必要です"}, status=400)

        # セッションを検証
        if not pairing_manager.validate_session(session_id):
            return JsonResponse({"error": "無効なセッションID"}, status=400)

        # コマンドを処理
        if command == 'chord_change':
            chord = params.get('chord')
            if chord:
                set_state(session_id, 'current_chord', chord)
                set_state(session_id, 'timestamp', int(request.headers.get('X-Timestamp', 0)))
                logger.info(f"コード変更: session_id={session_id}, chord={chord}")

        elif command == 'practice_start':
            set_state(session_id, 'is_practice', True)
            set_state(session_id, 'timestamp', int(request.headers.get('X-Timestamp', 0)))
            logger.info(f"練習開始: session_id={session_id}")

        elif command == 'practice_end':
            set_state(session_id, 'is_practice', False)
            set_state(session_id, 'timestamp', int(request.headers.get('X-Timestamp', 0)))
            logger.info(f"練習終了: session_id={session_id}")

        else:
            return JsonResponse({"error": f"未知のコマンド: {command}"}, status=400)

        return JsonResponse({"success": True, "message": "コマンドを受信しました"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "無効なJSON形式"}, status=400)
    except Exception as e:
        logger.error(f"コマンド処理エラー: {e}", exc_info=True)
        return JsonResponse({"error": "サーバーエラー"}, status=500)
