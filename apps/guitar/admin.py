"""
Admin configuration for guitar models
"""

from django.contrib import admin
from .models import Chord


@admin.register(Chord)
class ChordAdmin(admin.ModelAdmin):
    """コードモデルの管理インターフェース"""

    list_display = ["name", "difficulty", "display_order", "created_at"]
    list_filter = ["difficulty", "created_at"]
    search_fields = ["name"]
    ordering = ["display_order", "name"]
    readonly_fields = ["created_at"]
