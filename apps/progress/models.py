"""
Progress models for VirtuTune

練習セッションとユーザーのコード習熟度に関するモデル定義
"""

from django.db import models
from django.conf import settings


class PracticeSession(models.Model):
    """
    練習セッションモデル

    ユーザーの練習記録を管理する
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="ユーザー",
        related_name="practice_sessions",
    )

    started_at = models.DateTimeField(verbose_name="開始日時")

    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="終了日時")

    duration_minutes = models.IntegerField(default=0, verbose_name="練習時間（分）")

    chords_practiced = models.JSONField(default=list, verbose_name="練習したコード")

    goal_achieved = models.BooleanField(
        null=True, blank=True, verbose_name="目標達成フラグ"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        db_table = "practice_sessions"
        verbose_name = "練習セッション"
        verbose_name_plural = "練習セッション"
        indexes = [
            models.Index(fields=["user"], name="idx_practice_user"),
            models.Index(fields=["started_at"], name="idx_practice_started"),
        ]
        ordering = ["-started_at"]

    def __str__(self):
        started_str = self.started_at.strftime("%Y-%m-%d %H:%M")
        return f"{self.user.username} - {started_str} (ID: {self.id})"


class UserChord(models.Model):
    """
    ユーザー別コード習熟度モデル

    ユーザーが各コードをどれくらい練習したかを追跡する
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="ユーザー",
        related_name="user_chords",
    )

    chord = models.ForeignKey(
        "guitar.Chord",
        on_delete=models.CASCADE,
        verbose_name="コード",
        related_name="user_chords",
    )

    practice_count = models.IntegerField(default=0, verbose_name="練習回数")

    last_practiced_at = models.DateTimeField(
        null=True, blank=True, verbose_name="最終練習日時"
    )

    proficiency_level = models.SmallIntegerField(default=0, verbose_name="習熟度レベル")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        db_table = "user_chords"
        verbose_name = "ユーザーコード"
        verbose_name_plural = "ユーザーコード"
        unique_together = [["user", "chord"]]
        ordering = ["user", "-proficiency_level", "chord"]

    def __str__(self):
        return (
            f"{self.user.username} - {self.chord.name} "
            f"(習熟度: {self.proficiency_level})"
        )
