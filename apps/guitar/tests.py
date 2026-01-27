"""
Tests for Chord model

テスト駆動開発でコードモデルを実装する
"""

from django.test import TestCase
from apps.guitar.models import Chord


class ChordModelTest(TestCase):
    """Chordモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.chord_data = {
            "name": "C",
            "finger_positions": {"E": 0, "A": 3, "D": 2, "G": 0, "B": 1, "e": 0},
            "difficulty": 1,
            "diagram": "x32010",
            "display_order": 1,
        }

    def test_create_chord_with_minimal_fields(self):
        """最小限のフィールドでコードを作成できること"""
        chord = Chord.objects.create(
            name="Am", finger_positions={"E": 0, "A": 0, "D": 2, "G": 2, "B": 1, "e": 0}
        )
        self.assertEqual(chord.name, "Am")
        self.assertEqual(chord.difficulty, 1)  # デフォルト値
        self.assertEqual(chord.display_order, 0)  # デフォルト値
        self.assertIsNotNone(chord.created_at)

    def test_create_chord_with_all_fields(self):
        """すべてのフィールドでコードを作成できること"""
        chord = Chord.objects.create(**self.chord_data)
        self.assertEqual(chord.name, "C")
        self.assertEqual(chord.finger_positions["A"], 3)
        self.assertEqual(chord.difficulty, 1)
        self.assertEqual(chord.diagram, "x32010")
        self.assertEqual(chord.display_order, 1)

    def test_chord_name_must_be_unique(self):
        """コード名は一意でなければならない"""
        Chord.objects.create(name="G", finger_positions={"E": 3})
        with self.assertRaises(Exception):
            Chord.objects.create(name="G", finger_positions={"E": 3})

    def test_chord_ordering(self):
        """コードがdisplay_orderとnameで順序付けられること"""
        Chord.objects.create(name="D", display_order=2, finger_positions={"E": 0})
        Chord.objects.create(name="A", display_order=1, finger_positions={"E": 0})
        Chord.objects.create(name="B", display_order=1, finger_positions={"E": 0})

        chords = list(Chord.objects.all())
        self.assertEqual(chords[0].name, "A")
        self.assertEqual(chords[1].name, "B")
        self.assertEqual(chords[2].name, "D")

    def test_chord_str_representation(self):
        """コードの文字列表現が名前であること"""
        chord = Chord.objects.create(name="F", finger_positions={"E": 1})
        self.assertEqual(str(chord), "F")

    def test_chord_db_table_name(self):
        """データベーステーブル名が正しいこと"""
        self.assertEqual(Chord._meta.db_table, "chords")

    def test_finger_positions_stores_json(self):
        """フィンガーポジションがJSONとして保存されること"""
        positions = {"E": 0, "A": 2, "D": 2, "G": 1, "B": 0, "e": 0}
        chord = Chord.objects.create(name="Em", finger_positions=positions)
        self.assertEqual(chord.finger_positions, positions)

    def test_diagram_can_be_blank(self):
        """ダイアグラムフィールドは空白でも可"""
        chord = Chord.objects.create(name="Dm", finger_positions={"E": 0}, diagram="")
        self.assertEqual(chord.diagram, "")

    def test_difficulty_default_value(self):
        """難易度のデフォルト値が1であること"""
        chord = Chord.objects.create(name="E", finger_positions={"E": 0})
        self.assertEqual(chord.difficulty, 1)

    def test_display_order_default_value(self):
        """表示順序のデフォルト値が0であること"""
        chord = Chord.objects.create(name="Fm", finger_positions={"E": 1})
        self.assertEqual(chord.display_order, 0)
