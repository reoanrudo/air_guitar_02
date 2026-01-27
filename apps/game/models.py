"""
Game models for VirtuTune

ゲーム機能のモデル定義
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Song(models.Model):
    """
    楽曲モデル

    ゲームでプレイできる楽曲の情報を管理する
    """

    name = models.CharField(max_length=255, unique=True, verbose_name="曲名")
    artist = models.CharField(max_length=255, verbose_name="アーティスト名")
    difficulty = models.IntegerField(default=1, verbose_name="難易度（1-5）")
    tempo = models.IntegerField(default=120, verbose_name="テンポ（BPM）")
    notes = models.JSONField(default=list, verbose_name="ノートシーケンス")
    duration_seconds = models.IntegerField(default=0, verbose_name="曲の長さ（秒）")
    display_order = models.SmallIntegerField(default=0, verbose_name="表示順序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        db_table = "songs"
        verbose_name = "楽曲"
        verbose_name_plural = "楽曲"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} - {self.artist}"


class SongNote(models.Model):
    """
    楽曲ノートモデル

    楽曲を構成する個別のノート情報を管理する
    """

    song = models.ForeignKey(
        Song, on_delete=models.CASCADE, related_name="song_notes", verbose_name="楽曲"
    )
    note_number = models.IntegerField(verbose_name="ノート番号（MIDI）")
    timing = models.FloatField(verbose_name="タイミング（秒）")
    note_name = models.CharField(max_length=10, verbose_name="ノート名")
    duration = models.FloatField(default=0.5, verbose_name="持続時間（秒）")

    class Meta:
        db_table = "song_notes"
        verbose_name = "楽曲ノート"
        verbose_name_plural = "楽曲ノート"
        ordering = ["song", "timing"]

    def __str__(self):
        return f"{self.note_name} at {self.timing}s ({self.song.name})"


class GameSession(models.Model):
    """
    ゲームセッションモデル

    ユーザーのゲームプレイセッションを記録する
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name="楽曲")
    score = models.IntegerField(default=0, verbose_name="スコア")
    max_combo = models.IntegerField(default=0, verbose_name="最大コンボ数")
    perfect_count = models.IntegerField(default=0, verbose_name="パーフェクト数")
    great_count = models.IntegerField(default=0, verbose_name="グレート数")
    good_count = models.IntegerField(default=0, verbose_name="グッド数")
    miss_count = models.IntegerField(default=0, verbose_name="ミス数")
    accuracy = models.FloatField(default=0.0, verbose_name="精度（%）")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="プレイ日時")

    class Meta:
        db_table = "game_sessions"
        verbose_name = "ゲームセッション"
        verbose_name_plural = "ゲームセッション"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.song.name} ({self.score} points)"


class Score(models.Model):
    """
    スコアモデル

    ユーザーの日次スコアを記録し、ランキング用に使用する
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name="楽曲")
    score = models.IntegerField(default=0, verbose_name="スコア")
    date = models.DateField(verbose_name="日付")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        db_table = "scores"
        verbose_name = "スコア"
        verbose_name_plural = "スコア"
        unique_together = [["user", "song", "date"]]
        ordering = ["-date", "-score"]

    def __str__(self):
        return f"{self.user.username} - {self.song.name}: {self.score} ({self.date})"


class Achievement(models.Model):
    """
    実績モデル

    ユーザーが達成できる実績を定義する
    """

    ACHIEVEMENT_TIERS = (
        (1, "ブロンズ"),
        (2, "シルバー"),
        (3, "ゴールド"),
    )

    name = models.CharField(max_length=50, unique=True, verbose_name="実績名")
    description = models.CharField(max_length=255, verbose_name="説明")
    icon_url = models.TextField(blank=True, verbose_name="アイコンURL")
    tier = models.SmallIntegerField(
        default=1, choices=ACHIEVEMENT_TIERS, verbose_name="ティア"
    )
    unlock_score = models.IntegerField(default=0, verbose_name="解除スコア")
    display_order = models.SmallIntegerField(default=0, verbose_name="表示順序")

    class Meta:
        db_table = "achievements"
        verbose_name = "実績"
        verbose_name_plural = "実績"
        ordering = ["display_order", "tier", "name"]

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """
    ユーザー実績モデル

    ユーザーが獲得した実績を記録する
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, verbose_name="実績"
    )
    unlocked_at = models.DateTimeField(auto_now_add=True, verbose_name="解除日時")

    class Meta:
        db_table = "user_achievements"
        verbose_name = "ユーザー実績"
        verbose_name_plural = "ユーザー実績"
        unique_together = [["user", "achievement"]]
        ordering = ["-unlocked_at"]

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
