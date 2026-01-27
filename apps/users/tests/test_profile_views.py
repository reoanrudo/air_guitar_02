"""
プロフィール管理ビューのテスト

プロフィール表示、更新、アカウント削除機能のテスト
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

User = get_user_model()


class ProfileViewTest(TestCase):
    """プロフィール表示ビューのテスト"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            daily_goal_minutes=30,
            streak_days=5,
            total_practice_minutes=150,
        )
        self.profile_url = reverse("users:profile")

    def test_profile_view_requires_login(self):
        """未ログインユーザーはログインページにリダイレクトされる"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/users/login/"))

    def test_profile_view_renders(self):
        """ログインユーザーはプロフィールページを表示できる"""
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_profile_view_shows_user_data(self):
        """プロフィールページにユーザーデータが表示される"""
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.profile_url)
        self.assertContains(response, "testuser")
        self.assertContains(response, "30")  # daily_goal_minutes
        self.assertContains(response, "5")  # streak_days
        self.assertContains(
            response, "2"
        )  # total_practice_hours (150 minutes = 2 hours)


class ProfileUpdateFormTest(TestCase):
    """プロフィール更新フォームのテスト"""

    def test_form_valid_data(self):
        """有効なデータでフォームがバリデートされる"""
        from apps.users.forms import ProfileUpdateForm

        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )
        data = {
            "username": "testuser",
            "daily_goal_minutes": 45,
            "reminder_enabled": True,
            "reminder_time": "19:00",
        }
        form = ProfileUpdateForm(data, instance=user)
        self.assertTrue(form.is_valid())

    def test_form_updates_user(self):
        """フォームがユーザー情報を更新する"""
        from apps.users.forms import ProfileUpdateForm

        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            daily_goal_minutes=30,
        )
        data = {
            "username": "testuser",
            "daily_goal_minutes": 60,
            "reminder_enabled": True,
            "reminder_time": "20:00",
        }
        form = ProfileUpdateForm(data, instance=user)
        if form.is_valid():
            updated_user = form.save()
            self.assertEqual(updated_user.daily_goal_minutes, 60)
            self.assertTrue(updated_user.reminder_enabled)
            self.assertEqual(str(updated_user.reminder_time), "20:00:00")


class ProfileUpdateViewTest(TestCase):
    """プロフィール更新ビューのテスト"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            daily_goal_minutes=30,
        )
        self.profile_update_url = reverse("users:profile_update")

    def test_profile_update_requires_login(self):
        """未ログインユーザーはログインページにリダイレクトされる"""
        response = self.client.get(self.profile_update_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/users/login/"))

    def test_profile_update_view_renders(self):
        """プロフィール更新ページが正しくレンダリングされる"""
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.profile_update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile_update.html")

    def test_profile_update_valid_data(self):
        """有効なデータでプロフィールが更新される"""
        self.client.login(username="testuser", password="testpassword123")
        data = {
            "username": "testuser",
            "daily_goal_minutes": 60,
            "reminder_enabled": True,
            "reminder_time": "21:00",
        }
        response = self.client.post(self.profile_update_url, data)
        self.assertEqual(response.status_code, 302)  # リダイレクト

        # ユーザー情報が更新されたか確認
        self.user.refresh_from_db()
        self.assertEqual(self.user.daily_goal_minutes, 60)
        self.assertTrue(self.user.reminder_enabled)
        self.assertEqual(str(self.user.reminder_time), "21:00:00")

        # 成功メッセージが表示されているか確認
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("プロフィールを更新しました", str(messages[0]))

    def test_profile_update_invalid_data(self):
        """無効なデータで更新が失敗する"""
        self.client.login(username="testuser", password="testpassword123")
        data = {
            "username": "",  # 空のユーザー名は無効
            "daily_goal_minutes": -10,  # 負の値は無効
        }
        response = self.client.post(self.profile_update_url, data)
        self.assertEqual(response.status_code, 200)  # 同じページに留まる

        # ユーザー情報が変更されていないことを確認
        self.user.refresh_from_db()
        self.assertEqual(self.user.daily_goal_minutes, 30)


class AccountDeleteViewTest(TestCase):
    """アカウント削除ビューのテスト"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )
        self.account_delete_url = reverse("users:account_delete")

    def test_account_delete_requires_login(self):
        """未ログインユーザーはログインページにリダイレクトされる"""
        response = self.client.get(self.account_delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/users/login/"))

    def test_account_delete_view_renders(self):
        """アカウント削除確認ページが正しくレンダリングされる"""
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.account_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/account_delete.html")

    def test_account_delete_with_correct_password(self):
        """正しいパスワードでアカウントが削除される"""
        self.client.login(username="testuser", password="testpassword123")
        user_id = self.user.id
        data = {"password": "testpassword123"}
        response = self.client.post(self.account_delete_url, data)

        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)

        # ユーザーが削除されたか確認
        self.assertFalse(User.objects.filter(id=user_id).exists())

        # ログアウトされているか確認
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_account_delete_with_wrong_password(self):
        """間違ったパスワードではアカウントが削除されない"""
        self.client.login(username="testuser", password="testpassword123")
        user_id = self.user.id
        data = {"password": "wrongpassword"}
        response = self.client.post(self.account_delete_url, data)
        self.assertEqual(response.status_code, 200)  # 同じページに留まる

        # ユーザーが削除されていないことを確認
        self.assertTrue(User.objects.filter(id=user_id).exists())

        # エラーメッセージが表示されているか確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("パスワードが正しくありません" in str(m) for m in messages))


class ProfileIntegrationTest(TestCase):
    """プロフィール管理機能の統合テスト"""

    def setUp(self):
        """テスト前のセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            daily_goal_minutes=30,
        )

    def test_complete_profile_management_flow(self):
        """プロフィール表示 → 更新 → 削除の完全なフロー"""
        # 1. プロフィール表示
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")

        # 2. プロフィール更新
        update_data = {
            "username": "testuser",
            "daily_goal_minutes": 45,
            "reminder_enabled": True,
            "reminder_time": "19:30",
        }
        response = self.client.post(reverse("users:profile_update"), update_data)
        self.assertEqual(response.status_code, 302)

        # 更新されたか確認
        self.user.refresh_from_db()
        self.assertEqual(self.user.daily_goal_minutes, 45)

        # 3. アカウント削除
        delete_data = {"password": "testpassword123"}
        response = self.client.post(reverse("users:account_delete"), delete_data)
        self.assertEqual(response.status_code, 302)

        # ユーザーが削除されたか確認
        self.assertFalse(User.objects.filter(username="testuser").exists())
