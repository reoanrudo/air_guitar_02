"""
Seed chords management command for VirtuTune

基本コードデータをシードする管理コマンド
"""

from django.core.management.base import BaseCommand
from apps.guitar.models import Chord


class Command(BaseCommand):
    """
    基本コードデータをデータベースにシードするコマンド
    """

    help = "Seed basic guitar chords (C, G, Am, F, D, E, Em, A)"

    def handle(self, *args, **options):
        """
        コマンドの実行処理

        基本コード8種類のデータを作成または更新する
        """
        # 基本コードデータ
        chords_data = [
            {
                "name": "C",
                "finger_positions": {
                    "E2": 0,
                    "A2": 0,
                    "D2": 2,
                    "G1": 2,
                    "B1": 1,
                    "e1": 0,
                },
                "difficulty": 1,
                "display_order": 1,
            },
            {
                "name": "G",
                "finger_positions": {
                    "E2": 2,
                    "A2": 2,
                    "D2": 0,
                    "G1": 0,
                    "B1": 0,
                    "e1": 3,
                },
                "difficulty": 1,
                "display_order": 2,
            },
            {
                "name": "Am",
                "finger_positions": {
                    "E2": 0,
                    "A2": 0,
                    "D2": 2,
                    "G1": 2,
                    "B1": 1,
                    "e1": 0,
                },
                "difficulty": 1,
                "display_order": 3,
            },
            {
                "name": "F",
                "finger_positions": {
                    "E2": 1,
                    "A2": 1,
                    "D2": 2,
                    "G1": 3,
                    "B1": 1,
                    "e1": 1,
                },
                "difficulty": 3,
                "display_order": 4,
            },
            {
                "name": "D",
                "finger_positions": {
                    "E2": 0,
                    "A2": 0,
                    "D2": 0,
                    "G1": 2,
                    "B1": 3,
                    "e1": 2,
                },
                "difficulty": 1,
                "display_order": 5,
            },
            {
                "name": "E",
                "finger_positions": {
                    "E2": 0,
                    "A2": 2,
                    "D2": 2,
                    "G1": 1,
                    "B1": 0,
                    "e1": 0,
                },
                "difficulty": 1,
                "display_order": 6,
            },
            {
                "name": "Em",
                "finger_positions": {
                    "E2": 0,
                    "A2": 2,
                    "D2": 2,
                    "G1": 0,
                    "B1": 0,
                    "e1": 0,
                },
                "difficulty": 1,
                "display_order": 7,
            },
            {
                "name": "A",
                "finger_positions": {
                    "E2": 0,
                    "A2": 0,
                    "D2": 2,
                    "G1": 2,
                    "B1": 2,
                    "e1": 0,
                },
                "difficulty": 1,
                "display_order": 8,
            },
        ]

        # コードデータを作成または更新
        created_count = 0
        updated_count = 0

        for chord_data in chords_data:
            chord, created = Chord.objects.get_or_create(
                name=chord_data["name"],
                defaults={
                    "finger_positions": chord_data["finger_positions"],
                    "difficulty": chord_data["difficulty"],
                    "display_order": chord_data["display_order"],
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created chord: {chord.name}"))
            else:
                # 既存の場合は更新
                chord.finger_positions = chord_data["finger_positions"]
                chord.difficulty = chord_data["difficulty"]
                chord.display_order = chord_data["display_order"]
                chord.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated chord: {chord.name}"))

        # 結果を表示
        total = created_count + updated_count
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully seeded {total} chords "
                f"({created_count} created, {updated_count} updated)"
            )
        )
