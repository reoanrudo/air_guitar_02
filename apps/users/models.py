"""
User models for VirtuTune

カスタムユーザーモデルの定義
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    カスタムユーザーモデル

    DjangoのAbstractUserを拡張し、VirtuTune固有のフィールドを追加
    """

    # 練習目標設定
    daily_goal_minutes = models.IntegerField(
        default=5, verbose_name="1日の目標練習時間（分）"
    )

    # リマインダー設定
    reminder_enabled = models.BooleanField(
        default=False, verbose_name="リマインダー有効フラグ"
    )
    reminder_time = models.TimeField(
        null=True, blank=True, verbose_name="リマインダー送信時刻"
    )

    # 統計情報
    streak_days = models.IntegerField(default=0, verbose_name="連続練習日数")
    total_practice_minutes = models.IntegerField(
        default=0, verbose_name="総練習時間（分）"
    )
    last_practice_date = models.DateField(
        null=True, blank=True, verbose_name="最終練習日"
    )

    class Meta:
        db_table = "users"
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
        indexes = [
            models.Index(fields=["streak_days"], name="idx_streak"),
            models.Index(fields=["last_practice_date"], name="idx_last_practice"),
        ]

    def __str__(self):
        return self.username
