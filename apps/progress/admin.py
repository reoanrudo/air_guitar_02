"""
Admin configuration for progress models
"""

from django.contrib import admin
from .models import PracticeSession, UserChord


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    """練習セッションモデルの管理インターフェース"""

    list_display = [
        "id",
        "user",
        "started_at",
        "ended_at",
        "duration_minutes",
        "goal_achieved",
    ]
    list_filter = ["goal_achieved", "started_at"]
    search_fields = ["user__username"]
    readonly_fields = ["created_at"]
    date_hierarchy = "started_at"


@admin.register(UserChord)
class UserChordAdmin(admin.ModelAdmin):
    """ユーザーコードモデルの管理インターフェース"""

    list_display = [
        "user",
        "chord",
        "practice_count",
        "proficiency_level",
        "last_practiced_at",
    ]
    list_filter = ["proficiency_level", "last_practiced_at"]
    search_fields = ["user__username", "chord__name"]
    readonly_fields = ["created_at", "updated_at"]
