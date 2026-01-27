"""
Guitar models for VirtuTune

コード（和音）に関するモデル定義
"""

from django.db import models


class Chord(models.Model):
    """
    ギターコードモデル

    コードの指板位置、難易度、ダイアグラム情報を管理する
    """

    name = models.CharField(max_length=10, unique=True, verbose_name="コード名")

    finger_positions = models.JSONField(verbose_name="指板位置")

    difficulty = models.SmallIntegerField(default=1, verbose_name="難易度")

    diagram = models.TextField(blank=True, verbose_name="コードダイアグラム")

    display_order = models.SmallIntegerField(default=0, verbose_name="表示順序")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        db_table = "chords"
        verbose_name = "コード"
        verbose_name_plural = "コード"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
