# Reminders App - VirtuTune

## 概要

Remindersアプリは、VirtuTuneユーザーへの練習リマインダーとストリーク警告メールを送信するCeleryベースの非同期タスクシステムを提供します。

## 機能

### 1. 毎日リマインダー (Daily Reminders)

- **タスク名**: `apps.reminders.services.send_daily_reminders`
- **目的**: ユーザーが設定した時刻に練習リマインダーを送信
- **条件**:
  - `reminder_enabled=True` のユーザー
  - `reminder_time` が設定されている
  - 現在時刻が `reminder_time` の±1時間以内
  - 今日まだ練習していない

### 2. ストリーク警告 (Streak Warnings)

- **タスク名**: `apps.reminders.services.check_missed_practices`
- **目的**: 昨日練習していないユーザーにストリークが途切れる警告を送信
- **条件**:
  - `streak_days > 0` のユーザー
  - 昨日の練習記録がない

## セットアップ

### 1. 依存関係のインストール

```bash
pip install celery>=5.3
pip install django-celery-beat>=2.5
pip install redis>=5.0
```

### 2. 設定

`config/settings.py` に以下の設定が含まれていることを確認:

```python
INSTALLED_APPS = [
    # ...
    'django_celery_beat',
    'apps.reminders',
    # ...
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### 3. マイグレーション

```bash
python manage.py migrate
```

これにより、`django_celery_beat` のテーブルが作成されます。

## 使用方法

### Celery Workerを起動

```bash
celery -A config worker -l info
```

### Celery Beatを起動

```bash
celery -A config beat -l info
```

### テストコマンド

管理コマンドでリマインダー機能をテストできます:

```bash
# 毎日リマインダーをテスト
python manage.py test_reminders --type daily

# ストリーク警告をテスト
python manage.py test_reminders --type streak

# すべてのリマインダーをテスト
python manage.py test_reminders --type all
```

## Celery Beatスケジュール設定

### Django Adminで設定

1. Django Admin (`/admin/`) にアクセス
2. 「Periodic tasks」セクションに移動
3. 新しい periodic task を追加:

#### 毎日リマインダー (推奨: 毎時実行)

- **Name**: `Send Daily Reminders`
- **Task**: `apps.reminders.services.send_daily_reminders`
- **Enabled**: ✓
- **Interval**: `Every 1 hour`

#### ストリーク警告 (推奨: 毎朝9時実行)

- **Name**: `Check Missed Practices`
- **Task**: `apps.reminders.services.check_missed_practices`
- **Enabled**: ✓
- **Crontab**: `0 9 * * *` (毎日9:00)

### または、コードで設定 (config/settings.py)

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-daily-reminders': {
        'task': 'apps.reminders.services.send_daily_reminders',
        'schedule': crontab(minute='*'),  # 毎時実行（時刻チェックはタスク内で行う）
    },
    'check-missed-practices': {
        'task': 'apps.reminders.services.check_missed_practices',
        'schedule': crontab(hour=9, minute=0),  # 毎朝9:00
    },
}
```

## メールテンプレート

### reminder_email.html

毎日のリマインダーメールテンプレート。

**コンテキスト変数**:
- `user`: ユーザーオブジェクト
- `daily_goal_minutes`: 目標練習時間（分）
- `streak_days`: 連続練習日数

### streak_warning_email.html

ストリーク警告メールテンプレート。

**コンテキスト変数**:
- `user`: ユーザーオブジェクト
- `streak_days`: 現在のストリーク日数

## ユーザー設定

### プロフィール画面で設定

ユーザーはプロフィール設定画面で以下を設定できます:

1. **リマインダー有効/無効**: `reminder_enabled`
2. **リマインダー時刻**: `reminder_time` (HH:MM形式)

### 例

```python
from apps.users.models import User

user = User.objects.get(username='testuser')
user.reminder_enabled = True
user.reminder_time = time(9, 0)  # 9:00 AM
user.save()
```

## ログ

Celeryタスクの実行結果は以下のログに出力されます:

```python
logger = logging.getLogger(__name__)
logger.info(f"リマインダー送信成功: user_id={user.id}, email={user.email}")
logger.error(f"リマインダー送信失敗: user_id={user.id}, error={str(e)}")
```

## エラーハンドリング

- **リトライ**: メール送信失敗時、最大3回リトライ（60秒間隔）
- **エラーログ**: すべてのエラーがログに記録
- **継続処理**: 1ユーザーの送信失敗が他のユーザーに影響しない

## テスト

```bash
# すべてのテストを実行
pytest apps/reminders/tests/

# カバレッジレポート
pytest apps/reminders/tests/ --cov=apps.reminders --cov-report=html
```

## トラブルシューティング

### メールが送信されない

1. **Redisが起動しているか確認**:
   ```bash
   redis-cli ping
   ```

2. **Celery Workerが実行中か確認**:
   ```bash
   ps aux | grep celery
   ```

3. **Celery Beatが実行中か確認**:
   ```bash
   celery -A config beat -l info
   ```

4. **ユーザー設定を確認**:
   - `reminder_enabled=True` ?
   - `reminder_time` が設定されている?

5. **メールバックエンド設定を確認**:
   ```python
   # 開発環境: コンソール出力
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

   # 本番環境: SMTP
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   ```

### タスクが実行されない

1. **Periodic Taskが有効になっているか確認**:
   - Django Admin → Periodic tasks → 該当タスクの「Enabled」チェック

2. **Celery Beatログを確認**:
   ```bash
   celery -A config beat -l debug
   ```

3. **タスク名が正しいか確認**:
   - `apps.reminders.services.send_daily_reminders`
   - `apps.reminders.services.check_missed_practices`

## パフォーマンス

- **同時処理**: Celery workerの並列数に依存
- **推奨設定**: `celery -A config worker -c 4 -l info` (4プロセス)
- **メール送信**: 非同期で実行されるため、Webアプリのレスポンスに影響なし

## セキュリティ

- ユーザーのメールアドレスは認証済みのアカウントのみ使用
- メールテンプレートはHTMLエスケープ済み
- 個人情報のログ出力を最小限に抑制

## 今後の拡張

- [ ] Slack/ Discord通知対応
- [ ] モバイルプッシュ通知対応
- [ ] カスタマイズ可能なリマインダー頻度（毎日/毎週）
- [ ] 統計レポート（週間/月間サマリー）

## 関連ファイル

- `/Users/taguchireo/camp/python/air_guitar_02/apps/reminders/services.py` - Celeryタスク実装
- `/Users/taguchireo/camp/python/air_guitar_02/apps/reminders/templates/reminders/` - メールテンプレート
- `/Users/taguchireo/camp/python/air_guitar_02/config/celery.py` - Celery設定
- `/Users/taguchireo/camp/python/air_guitar_02/config/settings.py` - Django設定
