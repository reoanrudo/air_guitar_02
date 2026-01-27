"""
Game management commands tests for VirtuTune

seed_songs管理コマンドのテスト
"""

import pytest
from django.core.management import call_command
from apps.game.models import Song


@pytest.mark.django_db
class TestSeedSongsCommand:
    """seed_songsコマンドのテスト"""

    def test_seed_songs_creates_three_songs(self):
        """3つの楽曲が作成されることをテスト"""
        # コマンドを実行
        call_command("seed_songs")

        # 3つの楽曲が作成されていることを確認
        songs = Song.objects.all()
        assert songs.count() == 3

        # すべての楽曲名が存在することを確認
        song_names = [song.name for song in songs]
        expected_names = ["Twinkle Twinkle", "Ode to Joy", "London Bridge"]
        for name in expected_names:
            assert name in song_names

    def test_seed_songs_idempotent(self):
        """コマンドは冪等性を持つ（再実行してもエラーにならない）"""
        # 1回目の実行
        call_command("seed_songs")
        first_count = Song.objects.count()

        # 2回目の実行
        call_command("seed_songs")
        second_count = Song.objects.count()

        # 楽曲数が変わらないことを確認
        assert first_count == second_count
        assert second_count == 3

    def test_seed_songs_twinkle_twinkle_attributes(self):
        """Twinkle Twinkleの楽曲属性が正しく設定されていることをテスト"""
        call_command("seed_songs")

        # Twinkle Twinkleを取得
        song = Song.objects.get(name="Twinkle Twinkle")

        # 属性を確認
        assert song.artist == "Traditional"
        assert song.difficulty == 1
        assert song.tempo == 100
        assert song.display_order == 1

    def test_seed_songs_ode_to_joy_attributes(self):
        """Ode to Joyの楽曲属性が正しく設定されていることをテスト"""
        call_command("seed_songs")

        # Ode to Joyを取得
        song = Song.objects.get(name="Ode to Joy")

        # 属性を確認
        assert song.artist == "Beethoven"
        assert song.difficulty == 2
        assert song.tempo == 120
        assert song.display_order == 2

    def test_seed_songs_london_bridge_attributes(self):
        """London Bridgeの楽曲属性が正しく設定されていることをテスト"""
        call_command("seed_songs")

        # London Bridgeを取得
        song = Song.objects.get(name="London Bridge")

        # 属性を確認
        assert song.artist == "Traditional"
        assert song.difficulty == 1
        assert song.tempo == 110
        assert song.display_order == 3

    def test_seed_songs_twinkle_twinkle_notes(self):
        """Twinkle Twinkleのノートシーケンスが正しく作成されていることをテスト"""
        call_command("seed_songs")

        # Twinkle Twinkleを取得
        song = Song.objects.get(name="Twinkle Twinkle")

        # ノート数を確認
        notes = song.song_notes.all()
        assert notes.count() == 14

        # 最初のノートを確認
        first_note = notes.first()
        assert first_note.note_name == "C"
        assert first_note.timing == 0.0
        assert first_note.duration == 0.6

        # 2番目のノートを確認
        second_note = notes[1]
        assert second_note.note_name == "C"
        assert second_note.timing == 0.6
        assert second_note.duration == 0.6

    def test_seed_songs_ode_to_joy_notes(self):
        """Ode to Joyのノートシーケンスが正しく作成されていることをテスト"""
        call_command("seed_songs")

        # Ode to Joyを取得
        song = Song.objects.get(name="Ode to Joy")

        # ノート数を確認
        notes = song.song_notes.all()
        assert notes.count() == 15

        # 最初のノートを確認
        first_note = notes.first()
        assert first_note.note_name == "E"
        assert first_note.timing == 0.0
        assert first_note.duration == 0.5

    def test_seed_songs_london_bridge_notes(self):
        """London Bridgeのノートシーケンスが正しく作成されていることをテスト"""
        call_command("seed_songs")

        # London Bridgeを取得
        song = Song.objects.get(name="London Bridge")

        # ノート数を確認
        notes = song.song_notes.all()
        assert notes.count() == 7

        # 最初のノートを確認
        first_note = notes.first()
        assert first_note.note_name == "G"
        assert first_note.timing == 0.0
        assert first_note.duration == 0.55

    def test_seed_songs_notes_timing_increases(self):
        """すべてのノートがタイミング順に並んでいることをテスト"""
        call_command("seed_songs")

        # すべての楽曲のノートを確認
        for song in Song.objects.all():
            notes = list(song.song_notes.all())
            # タイミングが昇順であることを確認
            for i in range(len(notes) - 1):
                assert notes[i].timing < notes[i + 1].timing

    def test_seed_songs_json_notes_field_populated(self):
        """JSONフィールドのnotesが正しく設定されていることをテスト"""
        call_command("seed_songs")

        # Twinkle TwinkleのJSONノートを確認
        song = Song.objects.get(name="Twinkle Twinkle")
        assert isinstance(song.notes, list)
        assert len(song.notes) == 14
        assert song.notes[0]["note"] == "C"
        assert song.notes[0]["timing"] == 0.0
        assert song.notes[0]["duration"] == 0.6

    def test_seed_songs_duration_calculated(self):
        """曲の長さが正しく計算されていることをテスト"""
        call_command("seed_songs")

        # Twinkle Twinkleの長さを確認
        song = Song.objects.get(name="Twinkle Twinkle")
        # 最後のノートのタイミング + デュレーション
        last_note = song.song_notes.last()
        expected_min_duration = last_note.timing + last_note.duration
        assert song.duration_seconds >= int(expected_min_duration)
