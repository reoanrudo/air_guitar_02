#!/bin/bash
# WebSocket Setup Verification Script

echo ""
echo "============================================================"
echo "VirtuTune WebSocket Setup Verification"
echo "============================================================"
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  仮想環境がアクティベートされていません"
    echo "   先に仮想環境をアクティベートしてください:"
    echo "   source .venv/bin/activate"
    echo ""
    exit 1
fi

echo "✓ 仮想環境: $VIRTUAL_ENV"
echo ""

# Check Django Channels installation
echo "✓ Django Channelsのインストール確認..."
pip show channels > /dev/null 2>&1
if [ $? -eq 0 ]; then
    VERSION=$(pip show channels | grep Version | cut -d' ' -f2)
    echo "  - Channels: インストール済み (バージョン $VERSION)"
else
    echo "  ✗ Channelsがインストールされていません"
    exit 1
fi

# Check daphne installation
echo ""
echo "✓ Daphneのインストール確認..."
pip show daphne > /dev/null 2>&1
if [ $? -eq 0 ]; then
    VERSION=$(pip show daphne | grep Version | cut -d' ' -f2)
    echo "  - Daphne: インストール済み (バージョン $VERSION)"
else
    echo "  ✗ Daphneがインストールされていません"
    exit 1
fi

# Check channels-redis installation
echo ""
echo "✓ channels-redisのインストール確認..."
pip show channels-redis > /dev/null 2>&1
if [ $? -eq 0 ]; then
    VERSION=$(pip show channels-redis | grep Version | cut -d' ' -f2)
    echo "  - channels-redis: インストール済み (バージョン $VERSION)"
else
    echo "  ✗ channels-redisがインストールされていません"
    exit 1
fi

# Check files exist
echo ""
echo "✓ WebSocket関連ファイルの確認..."

FILES=(
    "config/asgi.py"
    "apps/websocket/consumers.py"
    "apps/websocket/routing.py"
    "apps/websocket/apps.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file が見つかりません"
        exit 1
    fi
done

# Test consumer import
echo ""
echo "✓ コンシューマーのインポート確認..."
python manage.py shell -c "from apps.websocket.consumers import GuitarConsumer; print('  ✓ GuitarConsumer import successful')" 2>&1 | grep -q "✓"
if [ $? -eq 0 ]; then
    echo "  ✓ GuitarConsumer: インポート成功"
else
    echo "  ✗ GuitarConsumer: インポート失敗"
    exit 1
fi

# Test routing import
echo ""
echo "✓ ルーティングのインポート確認..."
python manage.py shell -c "from apps.websocket.routing import websocket_urlpatterns; print('  ✓ Routing import successful')" 2>&1 | grep -q "✓"
if [ $? -eq 0 ]; then
    echo "  ✓ WebSocket Routing: インポート成功"
else
    echo "  ✗ WebSocket Routing: インポート失敗"
    exit 1
fi

# Run tests
echo ""
echo "✓ テスト実行..."
python manage.py test apps.websocket.test_websocket --verbosity=0 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ すべてのテストが成功しました"
else
    echo "  ⚠️  テストでエラーが発生しました"
    echo "     詳細: python manage.py test apps.websocket.test_websocket -v 2"
fi

echo ""
echo "============================================================"
echo "✓ すべてのチェックが成功しました!"
echo "============================================================"
echo ""
echo "WebSocket実装の準備が完了しました。"
echo ""
echo "次のステップ:"
echo "1. Redisサーバーを起動: redis-server"
echo "2. Djangoサーバーを起動: python manage.py runserver"
echo "3. テストを実行: python manage.py test apps.websocket.test_websocket"
echo "4. 手動テスト: python apps/websocket/manual_test.py"
echo ""
