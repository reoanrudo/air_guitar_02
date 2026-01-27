"""
Reminders app configuration
"""

from django.apps import AppConfig


class RemindersConfig(AppConfig):
    """リマインダーアプリの設定クラス"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reminders"
    verbose_name = "リマインダー"
