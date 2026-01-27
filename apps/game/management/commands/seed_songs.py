"""
Seed songs management command for VirtuTune

楽曲データをシードする管理コマンド
"""

from django.core.management.base import BaseCommand
from apps.game.models import Song, SongNote


class Command(BaseCommand):
    """
    楽曲データをデータベースにシードするコマンド
    """

    help = "Seed basic songs (Twinkle Twinkle, Ode to Joy, London Bridge)"

    def handle(self, *args, **options):
        """
        コマンドの実行処理

        3つの基本楽曲とそのノートデータを作成または更新する
        """
        # 楽曲データ
        songs_data = [
            {
                "name": "Twinkle Twinkle",
                "artist": "Traditional",
                "difficulty": 1,
                "tempo": 100,
                "display_order": 1,
                "notes": [
                    # タクト1: C, C, G, G
                    {"timing": 0.0, "note": "C", "note_number": 60, "duration": 0.6},
                    {"timing": 0.6, "note": "C", "note_number": 60, "duration": 0.6},
                    {"timing": 1.2, "note": "G", "note_number": 67, "duration": 0.6},
                    {"timing": 1.8, "note": "G", "note_number": 67, "duration": 0.6},
                    # タクト2: A, A, G
                    {"timing": 2.4, "note": "A", "note_number": 69, "duration": 0.6},
                    {"timing": 3.0, "note": "A", "note_number": 69, "duration": 0.6},
                    {"timing": 3.6, "note": "G", "note_number": 67, "duration": 1.2},
                    # タクト3: F, F, E, E
                    {"timing": 4.8, "note": "F", "note_number": 65, "duration": 0.6},
                    {"timing": 5.4, "note": "F", "note_number": 65, "duration": 0.6},
                    {"timing": 6.0, "note": "E", "note_number": 64, "duration": 0.6},
                    {"timing": 6.6, "note": "E", "note_number": 64, "duration": 0.6},
                    # タクト4: D, D, C
                    {"timing": 7.2, "note": "D", "note_number": 62, "duration": 0.6},
                    {"timing": 7.8, "note": "D", "note_number": 62, "duration": 0.6},
                    {"timing": 8.4, "note": "C", "note_number": 60, "duration": 1.2},
                ],
            },
            {
                "name": "Ode to Joy",
                "artist": "Beethoven",
                "difficulty": 2,
                "tempo": 120,
                "display_order": 2,
                "notes": [
                    # タクト1: E, E, F, G, G, F, E, D
                    {"timing": 0.0, "note": "E", "note_number": 64, "duration": 0.5},
                    {"timing": 0.5, "note": "E", "note_number": 64, "duration": 0.5},
                    {"timing": 1.0, "note": "F", "note_number": 65, "duration": 0.5},
                    {"timing": 1.5, "note": "G", "note_number": 67, "duration": 0.5},
                    {"timing": 2.0, "note": "G", "note_number": 67, "duration": 0.5},
                    {"timing": 2.5, "note": "F", "note_number": 65, "duration": 0.5},
                    {"timing": 3.0, "note": "E", "note_number": 64, "duration": 0.5},
                    {"timing": 3.5, "note": "D", "note_number": 62, "duration": 0.5},
                    # タクト2: C, C, D, E, E, D, D
                    {"timing": 4.0, "note": "C", "note_number": 60, "duration": 0.5},
                    {"timing": 4.5, "note": "C", "note_number": 60, "duration": 0.5},
                    {"timing": 5.0, "note": "D", "note_number": 62, "duration": 0.5},
                    {"timing": 5.5, "note": "E", "note_number": 64, "duration": 0.5},
                    {"timing": 6.0, "note": "E", "note_number": 64, "duration": 0.5},
                    {"timing": 6.5, "note": "D", "note_number": 62, "duration": 0.5},
                    {"timing": 7.0, "note": "D", "note_number": 62, "duration": 1.0},
                ],
            },
            {
                "name": "London Bridge",
                "artist": "Traditional",
                "difficulty": 1,
                "tempo": 110,
                "display_order": 3,
                "notes": [
                    # G, A, G, F, E, F, G (main melody)
                    {"timing": 0.0, "note": "G", "note_number": 67, "duration": 0.55},
                    {"timing": 0.55, "note": "A", "note_number": 69, "duration": 0.55},
                    {"timing": 1.1, "note": "G", "note_number": 67, "duration": 0.55},
                    {"timing": 1.65, "note": "F", "note_number": 65, "duration": 0.55},
                    {"timing": 2.2, "note": "E", "note_number": 64, "duration": 0.55},
                    {"timing": 2.75, "note": "F", "note_number": 65, "duration": 0.55},
                    {"timing": 3.3, "note": "G", "note_number": 67, "duration": 1.1},
                ],
            },
        ]

        # 楽曲データを作成または更新
        created_count = 0
        updated_count = 0

        for song_data in songs_data:
            notes_data = song_data.pop("notes")

            # 楽曲を作成または更新
            song, created = Song.objects.get_or_create(
                name=song_data["name"],
                defaults={
                    "artist": song_data["artist"],
                    "difficulty": song_data["difficulty"],
                    "tempo": song_data["tempo"],
                    "display_order": song_data["display_order"],
                    "notes": notes_data,
                    "duration_seconds": 0,  # 後で計算
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created song: {song.name}"))
            else:
                # 既存の場合は更新
                song.artist = song_data["artist"]
                song.difficulty = song_data["difficulty"]
                song.tempo = song_data["tempo"]
                song.display_order = song_data["display_order"]
                song.notes = notes_data
                song.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated song: {song.name}"))

            # 既存のノートを削除して再作成（冪等性を保証）
            song.song_notes.all().delete()

            # ノートデータを作成
            for idx, note_data in enumerate(notes_data):
                SongNote.objects.create(
                    song=song,
                    note_number=note_data["note_number"],
                    note_name=note_data["note"],
                    timing=note_data["timing"],
                    duration=note_data["duration"],
                )

            # 曲の長さを計算（最後のノートのタイミング + デュレーション）
            if notes_data:
                last_note = notes_data[-1]
                song.duration_seconds = int(last_note["timing"] + last_note["duration"])
                song.save()

        # 結果を表示
        total = created_count + updated_count
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully seeded {total} songs "
                f"({created_count} created, {updated_count} updated)"
            )
        )
