"""
Guitar views tests for VirtuTune

仮想ギタービューのテスト
"""

import pytest
import json
from django.urls import reverse
from apps.guitar.models import Chord
from apps.progress.models import PracticeSession


@pytest.mark.django_db
class TestGuitarView:
    """GuitarViewのテスト"""

    def test_guitar_view_requires_login(self, client):
        """未ログインユーザーはログインページにリダイレクトされる"""
        url = reverse("guitar:guitar")
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith("/users/login/")

    def test_guitar_view_renders_for_logged_in_user(self, client, django_user_model):
        """ログインユーザーはギターページを表示できる"""
        # テストユーザーを作成してログイン
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:guitar")
        response = client.get(url)

        assert response.status_code == 200
        assert "guitar/guitar.html" in [t.name for t in response.templates]
        assert "chords" in response.context

    def test_guitar_view_passes_chords_to_context(self, client, django_user_model):
        """ビューはコードデータをコンテキストに渡す"""
        # テストユーザーを作成してログイン
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        # テスト用コードデータを作成
        Chord.objects.create(
            name="C",
            finger_positions={"E2": 0, "A2": 0, "D2": 2, "G1": 2, "B1": 1, "e1": 0},
            display_order=1,
        )
        Chord.objects.create(
            name="G",
            finger_positions={"E2": 2, "A2": 2, "D2": 0, "G1": 0, "B1": 0, "e1": 3},
            display_order=2,
        )

        url = reverse("guitar:guitar")
        response = client.get(url)

        assert response.status_code == 200
        chords = response.context["chords"]
        assert chords.count() == 2
        assert chords.first().name == "C"
        assert chords.last().name == "G"

    def test_guitar_page_contains_required_elements(self, client, django_user_model):
        """ギターページに必要な要素が含まれている"""
        # テストユーザーを作成してログイン
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:guitar")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # 必要な要素の存在を確認
        assert "guitar-container" in content
        assert "guitar-neck" in content
        assert "string" in content
        assert "chord-selector" in content
        assert "practice-controls" in content
        assert "start-practice" in content
        assert "stop-practice" in content
        assert "timer" in content

    def test_guitar_page_contains_visual_feedback_elements(
        self, client, django_user_model
    ):
        """ギターページにビジュアルフィードバック要素が含まれている"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:guitar")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # ビジュアルフィードバック要素の存在を確認
        assert "audio-visualizer" in content
        assert "visualizer.js" in content


@pytest.mark.django_db
class TestStartPracticeAPI:
    """start_practice APIのテスト"""

    def test_start_practice_requires_authentication(self, client):
        """未ログインユーザーはログインページにリダイレクトされる"""
        url = reverse("guitar:start_practice")
        response = client.post(url)

        assert response.status_code == 302
        assert response.url.startswith("/users/login/")

    def test_start_practice_creates_session(self, client, django_user_model):
        """ログインユーザーは練習セッションを作成できる"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:start_practice")
        response = client.post(url)

        assert response.status_code == 201
        data = json.loads(response.content)
        assert "session_id" in data
        assert "started_at" in data

        # セッションがデータベースに保存されたことを確認
        session = PracticeSession.objects.get(id=data["session_id"])
        assert session.user == user
        assert session.ended_at is None

    def test_start_practice_returns_valid_session_data(self, client, django_user_model):
        """start_practiceは有効なセッションデータを返す"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:start_practice")
        response = client.post(url)

        assert response.status_code == 201
        data = json.loads(response.content)

        # レスポンスデータの検証
        assert isinstance(data["session_id"], int)
        assert "started_at" in data
        assert isinstance(data["started_at"], str)


@pytest.mark.django_db
class TestEndPracticeAPI:
    """end_practice APIのテスト"""

    def test_end_practice_requires_authentication(self, client):
        """未ログインユーザーはログインページにリダイレクトされる"""
        url = reverse("guitar:end_practice")
        response = client.post(
            url, data=json.dumps({}), content_type="application/json"
        )

        assert response.status_code == 302
        assert response.url.startswith("/users/login/")

    def test_end_practice_with_valid_session(self, client, django_user_model):
        """有効なセッションで練習を終了できる"""
        from django.utils import timezone

        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
            daily_goal_minutes=5,
            total_practice_minutes=100,
        )
        client.force_login(user)

        # セッションを作成
        session = PracticeSession.objects.create(user=user, started_at=timezone.now())

        url = reverse("guitar:end_practice")
        payload = {"session_id": session.id, "chords": ["C", "G", "Am"]}
        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        # セッションが更新されたことを確認
        session.refresh_from_db()
        assert session.ended_at is not None
        assert session.duration_minutes >= 0
        assert session.chords_practiced == ["C", "G", "Am"]

        # ユーザー統計が更新されたことを確認
        user.refresh_from_db()
        assert user.total_practice_minutes >= 100
        assert user.last_practice_date is not None

    def test_end_practice_with_invalid_session_id(self, client, django_user_model):
        """無効なセッションIDで400エラーを受信する"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:end_practice")
        payload = {"session_id": 99999, "chords": ["C"]}  # 存在しないID
        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_end_practice_with_empty_chords(self, client, django_user_model):
        """空のコードリストで練習を終了できる"""
        from django.utils import timezone

        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        session = PracticeSession.objects.create(user=user, started_at=timezone.now())
        url = reverse("guitar:end_practice")
        payload = {"session_id": session.id, "chords": []}
        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        session.refresh_from_db()
        assert session.chords_practiced == []

    def test_end_practice_calculates_goal_achieved(self, client, django_user_model):
        """goal_achievedが正しく計算される"""
        from django.utils import timezone
        from datetime import timedelta

        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123", daily_goal_minutes=5
        )
        client.force_login(user)

        # 10分前に開始されたセッションを作成
        started_time = timezone.now() - timedelta(minutes=10)
        session = PracticeSession.objects.create(user=user, started_at=started_time)
        url = reverse("guitar:end_practice")

        payload = {"session_id": session.id, "chords": ["C"]}
        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        session.refresh_from_db()
        # 10分 >= 5分なのでgoal_achievedはTrue
        assert session.goal_achieved is True

    def test_end_practice_requires_session_id(self, client, django_user_model):
        """session_idが必須であることを確認"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:end_practice")
        payload = {"chords": ["C"]}
        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400

    def test_end_practice_handles_malformed_json(self, client, django_user_model):
        """不正なJSONを処理できる"""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass123"
        )
        client.force_login(user)

        url = reverse("guitar:end_practice")
        response = client.post(
            url, data="invalid json", content_type="application/json"
        )

        assert response.status_code == 400
