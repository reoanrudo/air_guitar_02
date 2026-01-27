# =====================================================
# VirtuTune - pytest Configuration
# =====================================================

import pytest
from django.conf import settings


def pytest_configure():
    """pytest-django設定"""
    settings.DEBUG = False
    settings.TEMPLATES[0]['OPTIONS']['debug'] = False
