"""
URL configuration for users app
"""

from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "users"

urlpatterns = [
    # 開発用自動ログイン（シークレットURL）
    path("dev/auto_login/", views.dev_auto_login, name="dev_auto_login"),
    # ユーザー登録
    path("signup/", views.SignUpView.as_view(), name="signup"),
    # ログイン
    path("login/", views.CustomLoginView.as_view(), name="login"),
    # ログアウト
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    # プロフィール
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # プロフィール更新
    path("profile/update/", views.ProfileUpdateView.as_view(), name="profile_update"),
    # アカウント削除
    path("account/delete/", views.AccountDeleteView.as_view(), name="account_delete"),
    # パスワードリセット（Django標準ビューを使用）
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset.html",
            email_template_name="users/password_reset_email.html",
            success_url="/users/password_reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url="/users/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
