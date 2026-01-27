"""
Guitar management commands tests for VirtuTune

管理コマンドのテスト
"""

import pytest
from django.core.management import call_command
from apps.guitar.models import Chord


@pytest.mark.django_db
class TestSeedChordsCommand:
    """seed_chordsコマンドのテスト"""

    def test_seed_chords_creates_all_chords(self):
        """すべての基本コードが作成される"""
        # コマンドを実行
        call_command("seed_chords")

        # 8つのコードが作成されていることを確認
        chords = Chord.objects.all()
        assert chords.count() == 8

        # すべてのコード名が存在することを確認
        chord_names = [chord.name for chord in chords]
        expected_names = ["C", "G", "Am", "F", "D", "E", "Em", "A"]
        for name in expected_names:
            assert name in chord_names

    def test_seed_chords_idempotent(self):
        """コマンドは冪等性を持つ（再実行してもエラーにならない）"""
        # 1回目の実行
        call_command("seed_chords")
        first_count = Chord.objects.count()

        # 2回目の実行
        call_command("seed_chords")
        second_count = Chord.objects.count()

        # コード数が変わらないことを確認
        assert first_count == second_count
        assert second_count == 8

    def test_seed_chords_correct_finger_positions(self):
        """コードの指板位置が正しく設定されている"""
        call_command("seed_chords")

        # Cコードの指板位置を確認
        c_chord = Chord.objects.get(name="C")
        expected_positions = {"E2": 0, "A2": 0, "D2": 2, "G1": 2, "B1": 1, "e1": 0}
        assert c_chord.finger_positions == expected_positions

        # Gコードの指板位置を確認
        g_chord = Chord.objects.get(name="G")
        expected_positions = {"E2": 2, "A2": 2, "D2": 0, "G1": 0, "B1": 0, "e1": 3}
        assert g_chord.finger_positions == expected_positions
