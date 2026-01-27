from django.test import TestCase, Client
from django.urls import reverse


class LandingPageTestCase(TestCase):
    """ランディングページのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.client = Client()

    def test_landing_page_returns_200(self):
        """ランディングページが正常に表示されること"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_landing_page_uses_correct_template(self):
        """ランディングページが正しいテンプレートを使用すること"""
        response = self.client.get("/")
        self.assertTemplateUsed(response, "core/index.html")
        self.assertTemplateUsed(response, "core/base.html")

    def test_landing_page_contains_service_tagline(self):
        """ランディングページにサービスのキャッチフレーズが含まれていること"""
        response = self.client.get("/")
        self.assertContains(response, "VirtuTune")
        self.assertContains(response, "仮想ギター")

    def test_landing_page_contains_signup_button(self):
        """ランディングページに新規登録ボタンが含まれていること"""
        response = self.client.get("/")
        self.assertContains(response, "新規登録")
        self.assertContains(response, reverse("users:signup"))

    def test_landing_page_contains_login_button(self):
        """ランディングページにログインボタンが含まれていること"""
        response = self.client.get("/")
        self.assertContains(response, "ログイン")
        self.assertContains(response, reverse("users:login"))

    def test_landing_page_contains_feature_sections(self):
        """ランディングページにサービス機能の説明が含まれていること"""
        response = self.client.get("/")
        self.assertContains(response, "練習記録")
        self.assertContains(response, "進捗表示")

    def test_base_template_has_correct_structure(self):
        """ベーステンプレートが正しいHTML構造を持つこと"""
        response = self.client.get("/")
        self.assertContains(response, "<!DOCTYPE html>")
        self.assertContains(response, '<html lang="ja">')
        self.assertContains(response, '<meta charset="UTF-8">')
        self.assertContains(response, 'name="viewport"')

    def test_base_template_loads_static_files(self):
        """ベーステンプレートが静的ファイルを読み込んでいること"""
        response = self.client.get("/")
        self.assertContains(response, "/static/")
