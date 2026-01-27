# Generated migration for achievement master data

from django.db import migrations


def create_achievements(apps, schema_editor):
    """実績マスタデータを作成する"""

    Achievement = apps.get_model("game", "Achievement")

    achievements = [
        {
            "name": "FIRST_PLAY",
            "description": "最初の一曲をクリア",
            "tier": 1,
            "unlock_score": 0,
            "display_order": 1,
            "icon_url": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#cd7f32" stroke="#8b4513" stroke-width="3"/><text x="50" y="55" font-size="40" text-anchor="middle" fill="white">🎸</text></svg>',
        },
        {
            "name": "PERFECT_PLAY",
            "description": "パーフェクト精度でクリア",
            "tier": 3,
            "unlock_score": 2000,
            "display_order": 2,
            "icon_url": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#ffd700" stroke="#daa520" stroke-width="3"/><text x="50" y="55" font-size="40" text-anchor="middle" fill="white">⭐</text></svg>',
        },
        {
            "name": "STREAK_7",
            "description": "7日連続で練習",
            "tier": 2,
            "unlock_score": 500,
            "display_order": 3,
            "icon_url": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#c0c0c0" stroke="#808080" stroke-width="3"/><text x="50" y="55" font-size="40" text-anchor="middle" fill="white">🔥</text></svg>',
        },
        {
            "name": "SCORE_1000",
            "description": "1曲で1000点以上を獲得",
            "tier": 2,
            "unlock_score": 1000,
            "display_order": 4,
            "icon_url": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#c0c0c0" stroke="#808080" stroke-width="3"/><text x="50" y="55" font-size="40" text-anchor="middle" fill="white">💯</text></svg>',
        },
        {
            "name": "COMBO_MASTER",
            "description": "1曲で50コンボ以上達成",
            "tier": 2,
            "unlock_score": 800,
            "display_order": 5,
            "icon_url": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#c0c0c0" stroke="#808080" stroke-width="3"/><text x="50" y="55" font-size="40" text-anchor="middle" fill="white">💥</text></svg>',
        },
        {
            "name": "PRACTICE_HOUR",
            "description": "練習時間が60分に達する",
            "tier": 1,
            "unlock_score": 0,
            "display_order": 6,
            "icon_url": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#cd7f32" stroke="#8b4513" stroke-width="3"/><text x="50" y="55" font-size="40" text-anchor="middle" fill="white">⏱️</text></svg>',
        },
    ]

    for achievement_data in achievements:
        Achievement.objects.create(**achievement_data)


def remove_achievements(apps, schema_editor):
    """実績マスタデータを削除する"""

    Achievement = apps.get_model("game", "Achievement")
    Achievement.objects.all().delete()


class Migration(migrations.Migration):
    """実績マスタデータのマイグレーション"""

    dependencies = [
        ("game", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_achievements, remove_achievements)]
