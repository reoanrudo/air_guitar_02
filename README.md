# VirtuTune (ヴァーチュチューン)

楽器初心者のための仮想ギターと進捗管理機能を持つPython Webアプリケーション。

## 🎸 機能

- **仮想ギター演奏**: ブラウザでギターを演奏体験
- **スマホ+PC連携**: 左手（スマホ）でコード選択、右手（PCカメラ）でストローク判定
- **練習記録**: 練習時間の自動記録と進捗管理
- **リズムゲーム**: Guitar Hero風のゲームモード
- **ランキング**: 日次・週間ランキングと実績バッジシステム

## 🚀 クイックスタート

### 環境要件

- Python 3.11+
- Redis (WebSocket・Celery用)
- PostgreSQL (本番環境、開発はSQLite)

### インストール手順

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd air_guitar_02

# 2. 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 依存ライブラリをインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
# .envファイルを編集してSECRET_KEYなどを設定

# 5. データベースマイグレーション
python manage.py migrate

# 6. 開発サーバー起動
python manage.py runserver
```

http://localhost:8000 にアクセス

### 開発用追加ツール

```bash
# コードフォーマット (Black)
black .

# リンティング (flake8)
flake8 .

# テスト実行
pytest
```

## 📦 依存ライブラリ

### バックエンド

| ライブラリ | 用途 |
|-----------|------|
| Django 5.0+ | Webフレームワーク |
| channels | WebSocket通信 |
| celery | 非同期タスク（リマインダー） |
| qrcode | QRコード生成 |

### フロントエンド

| ライブラリ | 用途 |
|-----------|------|
| Chart.js | グラフ描画 |
| MediaPipe Hands | カメラジェスチャー認識 |

## 📁 プロジェクト構成

```
air_guitar_02/
├── config/           # Djangoプロジェクト設定
├── apps/
│   ├── core/         # コアアプリ
│   ├── guitar/       # 仮想ギター
│   ├── progress/     # 進捗管理
│   ├── users/        # ユーザー認証
│   ├── game/         # リズムゲーム
│   ├── ranking/      # ランキング
│   ├── mobile/       # モバイルAPI
│   └── websocket/    # WebSocket
├── static/           # 静的ファイル
└── requirements.txt
```

## 🔧 設定

環境変数は `.env` ファイルで設定します：

```bash
SECRET_KEY=your-secret-key
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

## 📝 ドキュメント

- [要件定義書](./requirements.md)
- [設計書](./design.md)
- [実装計画](./task.md)

## 🧪 テスト

```bash
pytest
```

## 📄 ライセンス

MIT License
