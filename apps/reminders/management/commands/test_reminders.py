"""
Test reminder management command

リマインダー機能をテストするための管理コマンド
"""

from django.core.management.base import BaseCommand

from apps.reminders.services import check_missed_practices, send_daily_reminders


class Command(BaseCommand):
    """リマインダーテストコマンド"""

    help = "Send test reminder emails to verify Celery task functionality"

    def add_arguments(self, parser):
        """コマンドライン引数を追加"""
        parser.add_argument(
            "--type",
            type=str,
            choices=["daily", "streak", "all"],
            default="all",
            help="Type of reminder to test: daily, streak, or all (default: all)",
        )

    def handle(self, *args, **options):
        """
        コマンドを実行する

        Args:
            *args: 位置引数
            **options: コマンドラインオプション
        """
        reminder_type = options["type"]

        self.stdout.write(self.style.SUCCESS("Testing reminder tasks..."))

        if reminder_type in ["daily", "all"]:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("Testing send_daily_reminders task...")
            self.stdout.write("=" * 50)

            try:
                result = send_daily_reminders()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ send_daily_reminders completed\n"
                        f"  - Sent: {result['sent_count']} emails\n"
                        f"  - Skipped: {result['skipped_count']} users\n"
                        f"  - Total users: {result['total_users']}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ send_daily_reminders failed: {str(e)}")
                )

        if reminder_type in ["streak", "all"]:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("Testing check_missed_practices task...")
            self.stdout.write("=" * 50)

            try:
                result = check_missed_practices()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ check_missed_practices completed\n"
                        f"  - Sent: {result['sent_count']} warnings\n"
                        f"  - Skipped: {result['skipped_count']} users\n"
                        f"  - Total missed: {result['total_missed']}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ check_missed_practices failed: {str(e)}")
                )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Test completed!")
        self.stdout.write("=" * 50)
