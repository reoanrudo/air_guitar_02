"""
Celery configuration for VirtuTune project.

非同期タスク（リマインダー送信など）の設定
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("virtutune")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
