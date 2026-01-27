"""
Tests for PracticeSession and UserChord models

テスト駆動開発で進捗管理モデルを実装する
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.progress.models import PracticeSession, UserChord
from apps.guitar.models import Chord

User = get_user_model()


class PracticeSessionModelTest(TestCase):
    """PracticeSessionモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session_data = {
            "user": self.user,
            "started_at": timezone.now(),
            "duration_minutes": 15,
            "chords_practiced": ["C", "Am", "F"],
            "goal_achieved": True,
        }

    def test_create_practice_session_with_minimal_fields(self):
        """最小限のフィールドで練習セッションを作成できること"""
        session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now()
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.duration_minutes, 0)  # デフォルト値
        self.assertEqual(session.chords_practiced, [])  # デフォルト値
        self.assertIsNone(session.ended_at)
        self.assertIsNone(session.goal_achieved)
        self.assertIsNotNone(session.created_at)

    def test_create_practice_session_with_all_fields(self):
        """すべてのフィールドで練習セッションを作成できること"""
        session = PracticeSession.objects.create(**self.session_data)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.duration_minutes, 15)
        self.assertEqual(session.chords_practiced, ["C", "Am", "F"])
        self.assertTrue(session.goal_achieved)

    def test_practice_session_with_ended_at(self):
        """終了時刻を設定できること"""
        started = timezone.now()
        ended = started + timedelta(minutes=10)
        session = PracticeSession.objects.create(
            user=self.user, started_at=started, ended_at=ended
        )
        self.assertIsNotNone(session.ended_at)

    def test_chords_practiced_stores_json_list(self):
        """練習したコードがJSONリストとして保存されること"""
        chords = ["C", "G", "Am", "F"]
        session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now(), chords_practiced=chords
        )
        self.assertEqual(session.chords_practiced, chords)

    def test_practice_session_db_table_name(self):
        """データベーステーブル名が正しいこと"""
        self.assertEqual(PracticeSession._meta.db_table, "practice_sessions")

    def test_practice_session_indexes(self):
        """インデックスが正しく設定されていること"""
        indexes = PracticeSession._meta.indexes
        self.assertTrue(len(indexes) > 0)

    def test_practice_session_str_representation(self):
        """練習セッションの文字列表現が適切であること"""
        session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now()
        )
        str_repr = str(session)
        self.assertIn(str(session.id), str_repr)
        self.assertIn(self.user.username, str_repr)

    def test_duration_minutes_default_value(self):
        """練習時間のデフォルト値が0であること"""
        session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now()
        )
        self.assertEqual(session.duration_minutes, 0)

    def test_goal_achieved_can_be_null(self):
        """目標達成フラグはnullでも可"""
        session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now(), goal_achieved=None
        )
        self.assertIsNone(session.goal_achieved)

    def test_goal_achieved_can_be_false(self):
        """目標未達成を記録できること"""
        session = PracticeSession.objects.create(
            user=self.user, started_at=timezone.now(), goal_achieved=False
        )
        self.assertFalse(session.goal_achieved)


class UserChordModelTest(TestCase):
    """UserChordモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.chord = Chord.objects.create(
            name="C", finger_positions={"E": 0, "A": 3, "D": 2, "G": 0, "B": 1, "e": 0}
        )

    def test_create_user_chord_with_minimal_fields(self):
        """最小限のフィールドでユーザーコードを作成できること"""
        user_chord = UserChord.objects.create(user=self.user, chord=self.chord)
        self.assertEqual(user_chord.user, self.user)
        self.assertEqual(user_chord.chord, self.chord)
        self.assertEqual(user_chord.practice_count, 0)  # デフォルト値
        self.assertIsNone(user_chord.last_practiced_at)
        self.assertEqual(user_chord.proficiency_level, 0)  # デフォルト値
        self.assertIsNotNone(user_chord.created_at)
        self.assertIsNotNone(user_chord.updated_at)

    def test_create_user_chord_with_all_fields(self):
        """すべてのフィールドでユーザーコードを作成できること"""
        now = timezone.now()
        user_chord = UserChord.objects.create(
            user=self.user,
            chord=self.chord,
            practice_count=5,
            last_practiced_at=now,
            proficiency_level=2,
        )
        self.assertEqual(user_chord.practice_count, 5)
        self.assertEqual(user_chord.proficiency_level, 2)

    def test_user_chord_unique_together(self):
        """ユーザーとコードの組み合わせは一意でなければならない"""
        UserChord.objects.create(user=self.user, chord=self.chord)
        with self.assertRaises(Exception):
            UserChord.objects.create(user=self.user, chord=self.chord)

    def test_user_chord_db_table_name(self):
        """データベーステーブル名が正しいこと"""
        self.assertEqual(UserChord._meta.db_table, "user_chords")

    def test_user_chord_str_representation(self):
        """ユーザーコードの文字列表現が適切であること"""
        user_chord = UserChord.objects.create(user=self.user, chord=self.chord)
        str_repr = str(user_chord)
        self.assertIn(self.user.username, str_repr)
        self.assertIn(self.chord.name, str_repr)

    def test_practice_count_default_value(self):
        """練習回数のデフォルト値が0であること"""
        user_chord = UserChord.objects.create(user=self.user, chord=self.chord)
        self.assertEqual(user_chord.practice_count, 0)

    def test_proficiency_level_default_value(self):
        """習熟度のデフォルト値が0であること"""
        user_chord = UserChord.objects.create(user=self.user, chord=self.chord)
        self.assertEqual(user_chord.proficiency_level, 0)

    def test_last_practiced_at_can_be_null(self):
        """最終練習日はnullでも可"""
        user_chord = UserChord.objects.create(user=self.user, chord=self.chord)
        self.assertIsNone(user_chord.last_practiced_at)

    def test_updated_at_auto_update(self):
        """updated_atが自動的に更新されること"""
        user_chord = UserChord.objects.create(user=self.user, chord=self.chord)
        original_updated_at = user_chord.updated_at
        user_chord.practice_count = 10
        user_chord.save()
        self.assertGreater(user_chord.updated_at, original_updated_at)

    def test_multiple_users_can_have_same_chord(self):
        """複数のユーザーが同じコードを持てること"""
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        _ = UserChord.objects.create(user=self.user, chord=self.chord)
        _ = UserChord.objects.create(user=user2, chord=self.chord)
        self.assertEqual(UserChord.objects.count(), 2)

    def test_user_can_have_multiple_chords(self):
        """ユーザーは複数のコードを持てること"""
        chord2 = Chord.objects.create(
            name="Am", finger_positions={"E": 0, "A": 0, "D": 2, "G": 2, "B": 1, "e": 0}
        )
        _ = UserChord.objects.create(user=self.user, chord=self.chord)
        _ = UserChord.objects.create(user=self.user, chord=chord2)
        self.assertEqual(UserChord.objects.filter(user=self.user).count(), 2)
