# WebSocket Implementation

## 概要

VirtuTuneのWebSocket機能は、スマートフォンとPCの間でのリアルタイム通信を実現します。

## アーキテクチャ

### コンポーネント

1. **GuitarConsumer** (`apps/websocket/consumers.py`)
   - AsyncWebsocketConsumerを継承
   - コード変更、練習開始/終了、接続管理を処理

2. **WebSocket Routing** (`apps/websocket/routing.py`)
   - URLパターン: `/ws/guitar/<session_id>/`
   - セッションIDに基づいたルーティング

3. **ASGI Application** (`config/asgi.py`)
   - HTTPとWebSocketのプロトコルルーティング
   - 認証ミドルウェアの統合

4. **Channel Layers** (`config/settings.py`)
   - Redisベースのチャネルレイヤー
   - 複数クライアント間のメッセージブロードキャスト

## サポートされるメッセージタイプ

### 1. chord_change
コード変更イベントを送受信

```json
{
  "type": "chord_change",
  "data": {
    "chord": "C"
  }
}
```

### 2. practice_start
練習開始イベント

```json
{
  "type": "practice_start",
  "data": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 3. practice_end
練習終了イベント

```json
{
  "type": "practice_end",
  "data": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 4. ping
接続確認（heart-beat）

```json
{
  "type": "ping",
  "data": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 5. pong
pingに対するレスポンス

```json
{
  "type": "pong",
  "data": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 6. connection_update
接続状態の更新通知

```json
{
  "type": "connection_update",
  "data": {
    "status": "connected|disconnected",
    "user_id": 1
  }
}
```

### 7. practice_update
練習状態の更新通知

```json
{
  "type": "practice_update",
  "data": {
    "status": "started|ended",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 8. error
エラーメッセージ

```json
{
  "type": "error",
  "data": {
    "message": "エラーの説明"
  }
}
```

## 接続フロー

### クライアント接続

1. クライアントが `/ws/guitar/<session_id>/` に接続
2. サーバーがセッションの有効性を検証
3. チャネルグループ `guitar_<session_id>` に参加
4. 接続通知をグループに送信
5. 接続確立

### メッセージ送信

1. クライアントがメッセージを送信
2. サーバーがメッセージタイプを解析
3. 適切なハンドラーで処理
4. グループ内の他のクライアントにブロードキャスト

### 切断

1. クライアントが切断
2. チャネルグループから退出
3. 切断通知をグループに送信

## 設定

### Redisの起動

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo systemctl start redis
```

### 環境変数

`.env`ファイルに設定:

```bash
REDIS_URL=redis://localhost:6379/0
```

## テスト

### 自動テスト

```bash
# すべてのWebSocketテストを実行
python manage.py test apps.websocket.test_websocket

# 詳細出力でテストを実行
python manage.py test apps.websocket.test_websocket -v 2
```

### 手動テスト

1. Django開発サーバーを起動:

```bash
python manage.py runserver
```

2. 別のターミナルで手動テストスクリプトを実行:

```bash
cd apps/websocket
python manual_test.py
```

## デプロイメント

### 本番環境での設定

1. **ASGIサーバー**:

Daphneを使用:

```bash
daphne config.asgi:application -b 0.0.0.0 -p 8001
```

2. **Nginx設定**:

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

3. **Redis**:

本番環境ではRedisを適切に設定し、永続化を有効にしてください。

## トラブルシューティング

### 接続が拒否される

- セッションIDが有効か確認
- ユーザーが認証されているか確認
- Redisが起動しているか確認

### メッセージが届かない

- チャネルレイヤーの設定を確認
- Redisの接続を確認
- ファイアウォール設定を確認

### パフォーマンス問題

- Redisのパフォーマンスを確認
- 接続数を確認
- チャネルレイヤーのバックログを確認

## セキュリティ

- 認証済みユーザーのみ接続可能
- セッションIDの検証
- CSRF保護（WebSocket接続時は不要）

## 今後の拡張

- 複数セッションの同時接続
- ルーム機能
- プレゼンス機能
- メッセージの永続化
- 再接続ロジックの強化
