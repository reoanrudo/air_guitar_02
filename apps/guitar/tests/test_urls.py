"""
Guitar URL configuration tests for VirtuTune

ギターアプリのURL設定のテスト
"""

import pytest
from django.urls import reverse, resolve


@pytest.mark.django_db
class TestGuitarURLs:
    """ギターURL設定のテスト"""

    def test_guitar_url_resolves_to_guitar_view(self):
        """ギターURLが正しく解決される"""
        url = reverse("guitar:guitar")
        resolve_match = resolve(url)
        assert resolve_match.url_name == "guitar"
        assert resolve_match.namespaces == ["guitar"]

    def test_guitar_url_path(self):
        """ギターURLのパスが正しい"""
        url = reverse("guitar:guitar")
        assert url == "/guitar/"
