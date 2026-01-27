"""
フォーム定義 for VirtuTune

ユーザー登録・認証に関連するフォーム
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    カスタムユーザー登録フォーム

    emailフィールドを追加したUserCreationForm
    """

    email = forms.EmailField(
        required=True,
        label="メールアドレス",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "your-email@example.com"}
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # フォームフィールドのスタイル設定
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "ユーザー名"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "パスワード"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "パスワード（確認）"}
        )

    def save(self, commit=True):
        """
        ユーザーを保存する

        Args:
            commit: データベースにコミットするかどうか

        Returns:
            保存されたユーザーインスタンス
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """
    プロフィール更新フォーム

    ユーザー情報の更新を行うフォーム
    """

    class Meta:
        model = User
        fields = ["username", "daily_goal_minutes", "reminder_enabled", "reminder_time"]
        widgets = {
            "reminder_time": forms.TimeInput(attrs={"type": "time"}),
            "daily_goal_minutes": forms.NumberInput(attrs={"min": "1", "max": "1440"}),
        }
        labels = {
            "username": "ユーザー名",
            "daily_goal_minutes": "1日の目標練習時間（分）",
            "reminder_enabled": "リマインダー有効",
            "reminder_time": "リマインダー時刻",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # フォームフィールドのスタイル設定
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["daily_goal_minutes"].widget.attrs.update({"class": "form-control"})
        self.fields["reminder_enabled"].widget.attrs.update(
            {"class": "form-check-input"}
        )
        self.fields["reminder_time"].widget.attrs.update({"class": "form-control"})

    def clean_daily_goal_minutes(self):
        """
        目標練習時間のバリデーション

        Returns:
            int: バリデーション済みの目標練習時間

        Raises:
            ValidationError: 値が不正な場合
        """
        minutes = self.cleaned_data.get("daily_goal_minutes")
        if minutes is not None and minutes <= 0:
            raise forms.ValidationError("目標練習時間は1分以上である必要があります。")
        if minutes is not None and minutes > 1440:
            raise forms.ValidationError(
                "目標練習時間は1440分（24時間）以下である必要があります。"
            )
        return minutes
