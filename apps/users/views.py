"""
ビュー定義 for VirtuTune

ユーザー認証に関連するビュー
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView, FormView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from .forms import CustomUserCreationForm, ProfileUpdateForm
from .models import User


class SignUpView(CreateView):
    """
    ユーザー登録ビュー

    登録成功後に自動的にログインし、ギター画面へリダイレクト
    """

    model = User
    form_class = CustomUserCreationForm
    template_name = "users/signup.html"

    def get_success_url(self):
        """
        登録成功後のリダイレクト先

        'guitar' URLが存在しない場合は 'users:login' にフォールバック

        Returns:
            str: リダイレクトURL
        """
        try:
            return reverse("guitar:guitar")
        except Exception:
            return reverse("users:login")

    def form_valid(self, form):
        """
        フォームが有効な場合の処理

        ユーザーを作成し、自動的にログインする

        Args:
            form: バリデーション済みフォーム

        Returns:
            HttpResponse
        """
        # ユーザーを保存
        self.object = form.save()

        # 自動ログイン
        login(self.request, self.object)
        messages.success(
            self.request, f"{self.object.username}さん、ようこそVirtuTuneへ！"
        )

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """
        フォームが無効な場合の処理

        エラーメッセージを表示

        Args:
            form: バリデーション失敗フォーム

        Returns:
            HttpResponse
        """
        messages.error(self.request, "登録に失敗しました。入力内容を確認してください。")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    """
    カスタムログインビュー

    AuthenticationFormを使用したログイン画面
    """

    form_class = AuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        ログイン成功後のリダイレクト先

        'guitar' URLが存在しない場合は 'users:login' にフォールバック

        Returns:
            str: リダイレクトURL
        """
        try:
            return reverse("guitar:guitar")
        except Exception:
            return reverse("users:login")

    def form_valid(self, form):
        """
        フォームが有効な場合の処理

        Args:
            form: バリデーション済みフォーム

        Returns:
            HttpResponse
        """
        messages.success(
            self.request, f"{form.get_user().username}さん、おかえりなさい！"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        フォームが無効な場合の処理

        Args:
            form: バリデーション失敗フォーム

        Returns:
            HttpResponse
        """
        messages.error(
            self.request,
            "ログインに失敗しました。ユーザー名とパスワードを確認してください。",
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """
    カスタムログアウトビュー
    """

    def get_next_page(self):
        """
        ログアウト後のリダイレクト先

        Returns:
            str: リダイレクトURL
        """
        return reverse("users:login")

    def dispatch(self, request, *args, **kwargs):
        """
        ログアウト処理

        Args:
            request: HttpRequest
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            HttpResponse
        """
        messages.info(request, "ログアウトしました。また遊びに来てください！")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    プロフィール表示ビュー

    ユーザーのプロフィール情報と統計データを表示する
    """

    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        """
        コンテキストデータを取得する

        ユーザー情報と統計データをテンプレートに渡す

        Args:
            **kwargs: キーワード引数

        Returns:
            dict: コンテキストデータ
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 統計情報を計算
        context["user"] = user
        context["streak_days"] = user.streak_days
        context["total_practice_minutes"] = user.total_practice_minutes
        context["total_practice_hours"] = user.total_practice_minutes // 60
        context["last_practice_date"] = user.last_practice_date

        return context


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """
    プロフィール更新ビュー

    ユーザーがプロフィール情報を更新するためのビュー
    """

    template_name = "users/profile_update.html"
    form_class = ProfileUpdateForm
    success_url = reverse_lazy("users:profile")
    success_message = "プロフィールを更新しました"

    def get_form_kwargs(self):
        """
        フォームに渡すキーワード引数を取得する

        現在のユーザーインスタンスをフォームに渡す

        Returns:
            dict: フォームのキーワード引数
        """
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        フォームが有効な場合の処理

        ユーザー情報を更新する

        Args:
            form: バリデーション済みフォーム

        Returns:
            HttpResponse
        """
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        フォームが無効な場合の処理

        エラーメッセージを表示

        Args:
            form: バリデーション失敗フォーム

        Returns:
            HttpResponse
        """
        messages.error(self.request, "入力内容を確認してください。")
        return super().form_invalid(form)


class AccountDeleteView(LoginRequiredMixin, TemplateView):
    """
    アカウント削除ビュー

    パスワード確認後にアカウントを削除する
    """

    template_name = "users/account_delete.html"

    def post(self, request, *args, **kwargs):
        """
        POSTリクエストの処理

        パスワードを確認し、アカウントを削除する

        Args:
            request: HttpRequest
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            HttpResponse
        """
        password = request.POST.get("password")

        # パスワードを確認
        if not request.user.check_password(password):
            messages.error(request, "パスワードが正しくありません。")
            return self.get(request, *args, **kwargs)

        # ユーザーを削除（関連データはカスケード削除）
        user = request.user
        username = user.username
        user.delete()

        # ログアウト
        from django.contrib.auth import logout

        logout(request)

        messages.success(request, f"{username}さんのアカウントを削除しました。")

        return redirect("users:login")


def dev_auto_login(request):
    """
    開発用自動ログインビュー（開発環境のみ）

    シークレットURLにアクセスするだけで自動的に管理者としてログイン

    Args:
        request: HttpRequest

    Returns:
        HttpResponse: ギター画面へリダイレクト
    """
    from django.conf import settings

    # 開発環境のみ許可
    if not settings.DEBUG:
        messages.error(request, "この機能は開発環境のみ使用可能です。")
        return redirect("users:login")

    # 管理者ユーザーを取得または作成
    from django.contrib.auth import get_user_model

    User = get_user_model()
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@virtutune.com",
            "is_staff": True,
            "is_superuser": True,
        },
    )

    # パスワードを設定（新規作成時のみ）
    if created:
        admin.set_password("admin123")
        admin.save()

    # 自動ログイン
    login(request, admin)
    messages.success(request, "開発用管理者として自動ログインしました！")

    return redirect("guitar:guitar")
