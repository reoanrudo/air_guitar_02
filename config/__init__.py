"""
VirtuTune Config Package

Celeryアプリケーションを初期化
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
