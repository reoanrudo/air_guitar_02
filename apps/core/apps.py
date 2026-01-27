from django.apps import AppConfig
from django.core.management import call_command


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        # 本番環境で自動マイグレーションを実行
        # 環境変数MIGRATE_ON_STARTUPが空でない場合のみ実行
        import os

        if os.environ.get("MIGRATE_ON_STARTUP"):
            try:
                call_command("migrate", "--noinput")

                # テスト用ユーザーを作成（まだ存在しない場合のみ）
                from apps.users.models import User

                if not User.objects.filter(username="test").exists():
                    User.objects.create_user(
                        username="test",
                        email="test@virtutune.com",
                        password="test123"
                    )
            except Exception:
                # マイグレーション失敗は静かに無視
                pass
