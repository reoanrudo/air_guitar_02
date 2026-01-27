"""
Game models tests for VirtuTune

ゲーム機能のモデルテスト
"""

from datetime import date

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.game.models import (
    Song,
    SongNote,
    GameSession,
    Score,
    Achievement,
    UserAchievement,
)

User = get_user_model()


class SongModelTest(TestCase):
    """Songモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=3,
            tempo=120,
            duration_seconds=180,
        )

    def test_song_creation(self):
        """Songモデルが正しく作成されること"""
        self.assertEqual(self.song.name, "Test Song")
        self.assertEqual(self.song.artist, "Test Artist")
        self.assertEqual(self.song.difficulty, 3)
        self.assertEqual(self.song.tempo, 120)
        self.assertEqual(self.song.duration_seconds, 180)
        self.assertEqual(self.song.notes, [])
        self.assertEqual(self.song.display_order, 0)

    def test_song_str_method(self):
        """Songの__str__メソッドが正しく動作すること"""
        self.assertEqual(str(self.song), "Test Song - Test Artist")

    def test_song_name_unique(self):
        """曲名は一意である必要があること"""
        with self.assertRaises(Exception):
            Song.objects.create(name="Test Song", artist="Another Artist")  # 重複

    def test_song_difficulty_range(self):
        """難易度は1-5の範囲内であること"""
        song_easy = Song.objects.create(name="Easy Song", artist="Artist", difficulty=1)
        self.assertEqual(song_easy.difficulty, 1)

        song_hard = Song.objects.create(name="Hard Song", artist="Artist", difficulty=5)
        self.assertEqual(song_hard.difficulty, 5)

    def test_song_notes_json_field(self):
        """notesフィールドにJSONデータを保存できること"""
        notes_data = [
            {"note": "C", "time": 0.5},
            {"note": "D", "time": 1.0},
            {"note": "E", "time": 1.5},
        ]
        self.song.notes = notes_data
        self.song.save()
        self.assertEqual(self.song.notes, notes_data)


class SongNoteModelTest(TestCase):
    """SongNoteモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.song = Song.objects.create(name="Test Song", artist="Test Artist")
        self.song_note = SongNote.objects.create(
            song=self.song, note_number=60, timing=1.5, note_name="C4", duration=0.5
        )

    def test_song_note_creation(self):
        """SongNoteモデルが正しく作成されること"""
        self.assertEqual(self.song_note.song, self.song)
        self.assertEqual(self.song_note.note_number, 60)
        self.assertEqual(self.song_note.timing, 1.5)
        self.assertEqual(self.song_note.note_name, "C4")
        self.assertEqual(self.song_note.duration, 0.5)

    def test_song_note_str_method(self):
        """SongNoteの__str__メソッドが正しく動作すること"""
        expected = "C4 at 1.5s (Test Song)"
        self.assertEqual(str(self.song_note), expected)

    def test_song_notes_related_name(self):
        """song_notes関連名でアクセスできること"""
        SongNote.objects.create(
            song=self.song, note_number=62, timing=2.0, note_name="D4"
        )
        self.assertEqual(self.song.song_notes.count(), 2)


class GameSessionModelTest(TestCase):
    """GameSessionモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.song = Song.objects.create(name="Test Song", artist="Test Artist")
        self.game_session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=1500,
            max_combo=10,
            perfect_count=20,
            great_count=15,
            good_count=5,
            miss_count=2,
            accuracy=95.5,
        )

    def test_game_session_creation(self):
        """GameSessionモデルが正しく作成されること"""
        self.assertEqual(self.game_session.user, self.user)
        self.assertEqual(self.game_session.song, self.song)
        self.assertEqual(self.game_session.score, 1500)
        self.assertEqual(self.game_session.max_combo, 10)
        self.assertEqual(self.game_session.perfect_count, 20)
        self.assertEqual(self.game_session.great_count, 15)
        self.assertEqual(self.game_session.good_count, 5)
        self.assertEqual(self.game_session.miss_count, 2)
        self.assertEqual(self.game_session.accuracy, 95.5)

    def test_game_session_str_method(self):
        """GameSessionの__str__メソッドが正しく動作すること"""
        expected = f"{self.user.username} - Test Song (1500 points)"
        self.assertEqual(str(self.game_session), expected)

    def test_game_session_defaults(self):
        """デフォルト値が正しく設定されること"""
        session = GameSession.objects.create(user=self.user, song=self.song)
        self.assertEqual(session.score, 0)
        self.assertEqual(session.max_combo, 0)
        self.assertEqual(session.perfect_count, 0)
        self.assertEqual(session.great_count, 0)
        self.assertEqual(session.good_count, 0)
        self.assertEqual(session.miss_count, 0)
        self.assertEqual(session.accuracy, 0.0)

    def test_game_session_user_relationship(self):
        """ユーザーに関連付けられたゲームセッションを取得できること"""
        GameSession.objects.create(user=self.user, song=self.song, score=2000)
        self.assertEqual(self.user.gamesession_set.count(), 2)


class ScoreModelTest(TestCase):
    """Scoreモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.song = Song.objects.create(name="Test Song", artist="Test Artist")
        self.test_date = date(2026, 1, 27)
        self.score = Score.objects.create(
            user=self.user, song=self.song, score=2500, date=self.test_date
        )

    def test_score_creation(self):
        """Scoreモデルが正しく作成されること"""
        self.assertEqual(self.score.user, self.user)
        self.assertEqual(self.score.song, self.song)
        self.assertEqual(self.score.score, 2500)
        self.assertEqual(self.score.date, self.test_date)

    def test_score_str_method(self):
        """Scoreの__str__メソッドが正しく動作すること"""
        expected = f"{self.user.username} - Test Song: 2500 (2026-01-27)"
        self.assertEqual(str(self.score), expected)

    def test_score_unique_together(self):
        """同じユーザー、曲、日付の組み合わせは一意であること"""
        # 同じ組み合わせで作成しようとすると失敗するはず
        with self.assertRaises(Exception):
            Score.objects.create(
                user=self.user,
                song=self.song,
                score=3000,
                date=self.test_date,  # 同じ日付
            )

    def test_score_different_dates_allowed(self):
        """異なる日付なら同じユーザーと曲で作成できること"""
        next_day = date(2026, 1, 28)
        score2 = Score.objects.create(
            user=self.user, song=self.song, score=3000, date=next_day
        )
        self.assertEqual(score2.score, 3000)
        self.assertEqual(
            Score.objects.filter(user=self.user, song=self.song).count(), 2
        )


class AchievementModelTest(TestCase):
    """Achievementモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.achievement = Achievement.objects.create(
            name="First Steps",
            description="Complete your first song",
            icon_url="/static/achievements/first_steps.png",
            tier=1,
            unlock_score=100,
            display_order=1,
        )

    def test_achievement_creation(self):
        """Achievementモデルが正しく作成されること"""
        self.assertEqual(self.achievement.name, "First Steps")
        self.assertEqual(self.achievement.description, "Complete your first song")
        self.assertEqual(
            self.achievement.icon_url, "/static/achievements/first_steps.png"
        )
        self.assertEqual(self.achievement.tier, 1)
        self.assertEqual(self.achievement.unlock_score, 100)
        self.assertEqual(self.achievement.display_order, 1)

    def test_achievement_str_method(self):
        """Achievementの__str__メソッドが正しく動作すること"""
        self.assertEqual(str(self.achievement), "First Steps")

    def test_achievement_name_unique(self):
        """実績名は一意である必要があること"""
        with self.assertRaises(Exception):
            Achievement.objects.create(
                name="First Steps", description="Different description"  # 重複
            )

    def test_achievement_tier_values(self):
        """ティアは1-3の範囲内であること（ブロンズ、シルバー、ゴールド）"""
        bronze = Achievement.objects.create(
            name="Bronze Achievement", description="Bronze tier", tier=1
        )
        self.assertEqual(bronze.tier, 1)

        silver = Achievement.objects.create(
            name="Silver Achievement", description="Silver tier", tier=2
        )
        self.assertEqual(silver.tier, 2)

        gold = Achievement.objects.create(
            name="Gold Achievement", description="Gold tier", tier=3
        )
        self.assertEqual(gold.tier, 3)

    def test_achievement_blank_icon_url(self):
        """icon_urlは空白で可能であること"""
        achievement = Achievement.objects.create(
            name="No Icon Achievement", description="Achievement without icon", tier=1
        )
        self.assertEqual(achievement.icon_url, "")


class UserAchievementModelTest(TestCase):
    """UserAchievementモデルのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.achievement = Achievement.objects.create(
            name="First Steps", description="Complete your first song", tier=1
        )
        self.user_achievement = UserAchievement.objects.create(
            user=self.user, achievement=self.achievement
        )

    def test_user_achievement_creation(self):
        """UserAchievementモデルが正しく作成されること"""
        self.assertEqual(self.user_achievement.user, self.user)
        self.assertEqual(self.user_achievement.achievement, self.achievement)
        self.assertIsNotNone(self.user_achievement.unlocked_at)

    def test_user_achievement_str_method(self):
        """UserAchievementの__str__メソッドが正しく動作すること"""
        expected = f"{self.user.username} - First Steps"
        self.assertEqual(str(self.user_achievement), expected)

    def test_user_achievement_unique_together(self):
        """同じユーザーと実績の組み合わせは一意であること"""
        # 同じ組み合わせで作成しようとすると失敗するはず
        with self.assertRaises(Exception):
            UserAchievement.objects.create(user=self.user, achievement=self.achievement)

    def test_user_achievement_different_users(self):
        """異なるユーザーは同じ実績を獲得できること"""
        user2 = User.objects.create_user(username="testuser2", password="testpass123")
        user2_achievement = UserAchievement.objects.create(
            user=user2, achievement=self.achievement
        )
        self.assertEqual(user2_achievement.achievement, self.achievement)
        self.assertEqual(
            UserAchievement.objects.filter(achievement=self.achievement).count(), 2
        )

    def test_user_achievement_relationships(self):
        """ユーザーと実績の関連付けが正しく動作すること"""
        self.assertEqual(self.user.userachievement_set.count(), 1)
        self.assertEqual(self.achievement.userachievement_set.count(), 1)


class GameModelIntegrationTest(TestCase):
    """ゲームモデル全体の統合テスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_complete_game_flow(self):
        """完全なゲームフローのテスト"""
        # 1. 曲を作成
        song = Song.objects.create(
            name="Test Song", artist="Test Artist", difficulty=3, tempo=120
        )

        # 2. ノートを追加
        SongNote.objects.create(song=song, note_number=60, timing=1.0, note_name="C4")
        SongNote.objects.create(song=song, note_number=62, timing=1.5, note_name="D4")

        # 3. ゲームセッションを作成
        session = GameSession.objects.create(
            user=self.user,
            song=song,
            score=2000,
            perfect_count=30,
            great_count=10,
            good_count=5,
            miss_count=0,
            accuracy=98.5,
        )

        # 4. スコアを記録
        score = Score.objects.create(
            user=self.user, song=song, score=2000, date=date.today()
        )

        # 5. 実績をアンロック
        achievement = Achievement.objects.create(
            name="Perfect Game",
            description="Complete a song with 100% accuracy",
            tier=3,
            unlock_score=2000,
        )
        user_achievement = UserAchievement.objects.create(
            user=self.user, achievement=achievement
        )

        # 検証
        self.assertEqual(song.song_notes.count(), 2)
        self.assertEqual(session.score, 2000)
        self.assertEqual(score.score, 2000)
        self.assertEqual(user_achievement.achievement, achievement)

    def test_multiple_users_same_song(self):
        """複数のユーザーが同じ曲をプレイできること"""
        song = Song.objects.create(name="Popular Song", artist="Famous Artist")

        user1 = User.objects.create_user(username="user1", password="pass123")
        user2 = User.objects.create_user(username="user2", password="pass123")

        GameSession.objects.create(user=user1, song=song, score=1500)
        GameSession.objects.create(user=user2, song=song, score=2000)

        self.assertEqual(GameSession.objects.filter(song=song).count(), 2)

    def test_song_difficulty_ordering(self):
        """曲を難易度順に取得できること"""
        Song.objects.create(name="Easy", artist="A", difficulty=1, display_order=1)
        Song.objects.create(name="Hard", artist="B", difficulty=5, display_order=3)
        Song.objects.create(name="Medium", artist="C", difficulty=3, display_order=2)

        songs = Song.objects.order_by("display_order")
        self.assertEqual(songs[0].name, "Easy")
        self.assertEqual(songs[1].name, "Medium")
        self.assertEqual(songs[2].name, "Hard")


class GameViewTests(TestCase):
    """テスト: ゲームビュー

    ゲームモードのビュー機能をテストする
    """

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_login(self.user)


class GameListViewTest(TestCase):
    """ゲームリストビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        # テスト用楽曲データを作成
        self.song1 = Song.objects.create(
            name="Test Song 1",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[],
            duration_seconds=60,
            display_order=1,
        )
        self.song2 = Song.objects.create(
            name="Test Song 2",
            artist="Test Artist",
            difficulty=3,
            tempo=140,
            notes=[],
            duration_seconds=90,
            display_order=2,
        )

    def test_game_list_view_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse("game:game_list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/users/login/"))

    def test_game_list_view_returns_200(self):
        """ゲームリストページが正常に表示されることをテスト"""
        response = self.client.get(reverse("game:game_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_list.html")

    def test_game_list_view_displays_songs(self):
        """楽曲が正しく表示されることをテスト"""
        response = self.client.get(reverse("game:game_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Song 1")
        self.assertContains(response, "Test Song 2")
        self.assertContains(response, "Test Artist")

    def test_game_list_view_shows_difficulty(self):
        """難易度が正しく表示されることをテスト"""
        response = self.client.get(reverse("game:game_list"))
        self.assertContains(response, "難易度: 1")
        self.assertContains(response, "難易度: 3")


class GamePlayViewTest(TestCase):
    """ゲームプレイビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[
                {"timing": 0.0, "note": "C", "duration": 1.0},
                {"timing": 1.0, "note": "G", "duration": 1.0},
                {"timing": 2.0, "note": "Am", "duration": 1.0},
            ],
            duration_seconds=60,
            display_order=1,
        )

    def test_game_play_view_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.get(
            reverse("game:game_play", kwargs={"song_id": self.song.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_game_play_view_returns_200(self):
        """ゲームプレイページが正常に表示されることをテスト"""
        response = self.client.get(
            reverse("game:game_play", kwargs={"song_id": self.song.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_play.html")

    def test_game_play_view_contains_song_data(self):
        """楽曲データがコンテキストに含まれることをテスト"""
        response = self.client.get(
            reverse("game:game_play", kwargs={"song_id": self.song.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["song"], self.song)
        self.assertContains(response, "Test Song")
        self.assertContains(response, "Test Artist")

    def test_game_play_view_invalid_song_id(self):
        """無効な楽曲IDで404エラーになることをテスト"""
        response = self.client.get(reverse("game:game_play", kwargs={"song_id": 99999}))
        self.assertEqual(response.status_code, 404)


class SaveGameResultViewTest(TestCase):
    """ゲーム結果保存ビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[],
            duration_seconds=60,
            display_order=1,
        )

    def test_save_game_result_creates_session(self):
        """ゲームセッションが正しく作成されることをテスト"""
        response = self.client.post(
            reverse("game:save_result"),
            data={
                "song_id": self.song.id,
                "score": 1000,
                "max_combo": 10,
                "perfect_count": 5,
                "great_count": 3,
                "good_count": 2,
                "miss_count": 1,
                "accuracy": 85.5,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(GameSession.objects.count(), 1)

        session = GameSession.objects.first()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.song, self.song)
        self.assertEqual(session.score, 1000)
        self.assertEqual(session.max_combo, 10)
        self.assertEqual(session.perfect_count, 5)
        self.assertEqual(session.great_count, 3)
        self.assertEqual(session.good_count, 2)
        self.assertEqual(session.miss_count, 1)
        self.assertAlmostEqual(session.accuracy, 0.855)

    def test_save_game_result_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.post(
            reverse("game:save_result"),
            data={
                "song_id": self.song.id,
                "score": 1000,
                "max_combo": 10,
                "perfect_count": 5,
                "great_count": 3,
                "good_count": 2,
                "miss_count": 1,
                "accuracy": 85.5,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_save_game_result_invalid_data(self):
        """無効なデータで400エラーになることをテスト"""
        response = self.client.post(
            reverse("game:save_result"),
            data={
                "song_id": self.song.id,
                "score": "invalid",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class GameResultViewTest(TestCase):
    """ゲーム結果ビューのテスト"""

    def setUp(self):
        """テスト用データのセットアップ"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.song = Song.objects.create(
            name="Test Song",
            artist="Test Artist",
            difficulty=1,
            tempo=120,
            notes=[],
            duration_seconds=60,
            display_order=1,
        )

        self.session = GameSession.objects.create(
            user=self.user,
            song=self.song,
            score=1000,
            max_combo=10,
            perfect_count=5,
            great_count=3,
            good_count=2,
            miss_count=1,
            accuracy=85.5,
        )

    def test_game_result_view_requires_login(self):
        """ログイン必須であることをテスト"""
        self.client.logout()
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": self.session.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_game_result_view_returns_200(self):
        """ゲーム結果ページが正常に表示されることをテスト"""
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": self.session.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/game_result.html")

    def test_game_result_view_displays_stats(self):
        """統計情報が正しく表示されることをテスト"""
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": self.session.id})
        )
        self.assertContains(response, "1000")
        self.assertContains(response, "10")
        self.assertContains(response, "5")
        self.assertContains(response, "3")
        self.assertContains(response, "2")
        self.assertContains(response, "1")
        self.assertContains(response, "85.5")

    def test_game_result_view_unauthorized_session(self):
        """他ユーザーのセッションにアクセスできないことをテスト"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )

        # 他ユーザーのセッションを作成
        other_session = GameSession.objects.create(
            user=other_user,
            song=self.song,
            score=500,
            max_combo=5,
            perfect_count=2,
            great_count=1,
            good_count=1,
            miss_count=1,
            accuracy=70.0,
        )

        # 元のユーザーで他ユーザーのセッションにアクセス
        response = self.client.get(
            reverse("game:game_result", kwargs={"session_id": other_session.id})
        )
        self.assertEqual(response.status_code, 403)
