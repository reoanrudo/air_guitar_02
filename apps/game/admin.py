"""
Game admin configuration for VirtuTune

ゲーム機能の管理画面設定
"""

from django.contrib import admin
from .models import Song, SongNote, GameSession, Score, Achievement, UserAchievement


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    """楽曲モデルの管理画面"""

    list_display = [
        "name",
        "artist",
        "difficulty",
        "tempo",
        "duration_seconds",
        "display_order",
    ]
    list_filter = ["difficulty", "created_at"]
    search_fields = ["name", "artist"]
    ordering = ["display_order", "name"]
    fieldsets = (
        ("基本情報", {"fields": ("name", "artist", "display_order")}),
        ("楽曲詳細", {"fields": ("difficulty", "tempo", "duration_seconds", "notes")}),
        ("メタデータ", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at"]


@admin.register(SongNote)
class SongNoteAdmin(admin.ModelAdmin):
    """楽曲ノートモデルの管理画面"""

    list_display = ["song", "note_name", "note_number", "timing", "duration"]
    list_filter = ["song"]
    search_fields = ["song__name", "note_name"]
    ordering = ["song", "timing"]


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """ゲームセッションモデルの管理画面"""

    list_display = ["user", "song", "score", "max_combo", "accuracy", "created_at"]
    list_filter = ["created_at", "song"]
    search_fields = ["user__username", "song__name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("セッション情報", {"fields": ("user", "song", "created_at")}),
        ("スコア詳細", {"fields": ("score", "max_combo", "accuracy")}),
        (
            "判定カウント",
            {"fields": ("perfect_count", "great_count", "good_count", "miss_count")},
        ),
    )


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    """スコアモデルの管理画面"""

    list_display = ["user", "song", "score", "date", "created_at"]
    list_filter = ["date", "song"]
    search_fields = ["user__username", "song__name"]
    ordering = ["-date", "-score"]
    readonly_fields = ["created_at"]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """実績モデルの管理画面"""

    list_display = ["name", "tier", "unlock_score", "display_order"]
    list_filter = ["tier"]
    search_fields = ["name", "description"]
    ordering = ["display_order", "tier", "name"]

    fieldsets = (
        ("基本情報", {"fields": ("name", "description", "display_order")}),
        ("実績詳細", {"fields": ("tier", "unlock_score", "icon_url")}),
    )


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """ユーザー実績モデルの管理画面"""

    list_display = ["user", "achievement", "unlocked_at"]
    list_filter = ["achievement__tier", "unlocked_at"]
    search_fields = ["user__username", "achievement__name"]
    ordering = ["-unlocked_at"]
    readonly_fields = ["unlocked_at"]
