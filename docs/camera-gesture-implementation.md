# カメラジェスチャー認識実装ドキュメント

## 概要

このドキュメントは、VirtuTuneプロジェクトにおけるカメラジェスチャー認識機能の実装について説明します。

## 技術スタック

- **MediaPipe Hands**: Googleの手検出・追跡ライブラリ
- **MediaPipe Camera Utils**: カメラアクセスユーティリティ
- **JavaScript (ES6+)**: クライアントサイド実装
- **CustomEvent API**: ストロームイベントの通知

## アーキテクチャ

### ファイル構成

```
static/js/
├── camera.js              # メイン実装ファイル
└── tests/
    ├── camera.test.js     # テストファイル
    ├── camera.test.html   # テストランナー
    └── camera-demo.html   # デモページ
```

### GestureRecognizer クラス

```javascript
class GestureRecognizer {
    constructor()
    async startCamera(videoElement)
    stopCamera()
    onResults(results)
    isStrumming(current, previous)
    strumVelocity(landmarks)
    triggerNote(velocity)
    isActive()
}
```

## 機能詳細

### 1. カメラアクセス

- **権限リクエスト**: `navigator.mediaDevices.getUserMedia()`を使用
- **エラーハンドリング**: 権限拒否時の適切なエラーメッセージ表示
- **ストリーム管理**: ビデオ要素へのストリーム割り当て

### 2. 手検出

MediaPipe Handsの設定:
- **最大検出手数**: 1手（ストローク検出に集中）
- **モデル複雑さ**: 1（精度と速度のバランス）
- **検出信頼度**: 0.7（誤検出を抑制）
- **追跡信頼度**: 0.7（安定した追跡）

### 3. ストローク検出アルゴリズム

#### isStrumming メソッド

```javascript
isStrumming(current, previous) {
    if (!previous) return false;

    // 手首（landmark 0）のY座標の変化を検知
    const currentY = current[0].y;
    const previousY = previous[0].y;
    const velocity = currentY - previousY;

    // 下方向への動きでストロークと判定
    return velocity > 0.05; // 閾値は調整可能
}
```

**ロジック**:
1. 前回のランドマークがない場合はfalseを返す
2. 手首（landmark 0）のY座標の変化を計算
3. 下方向への動き（velocity > 0.05）をストロークと判定

#### strumVelocity メソッド

```javascript
strumVelocity(landmarks) {
    // 手首（landmark 0）と中指の先（landmark 12）の距離でVelocityを計算
    const wrist = landmarks[0];
    const middleTip = landmarks[12];

    const distance = Math.sqrt(
        Math.pow(wrist.x - middleTip.x, 2) +
        Math.pow(wrist.y - middleTip.y, 2)
    );

    // 0-1の範囲に正規化
    return Math.min(distance, 1.0);
}
```

**ロジック**:
1. 手首と中指の先のユークリッド距離を計算
2. 0-1の範囲に正規化して返す
3. この値は音の速度や強さとして使用可能

### 4. イベント通知

ストローク検出時にカスタムイベントを発火:

```javascript
window.dispatchEvent(new CustomEvent('strum', {
    detail: { velocity }
}));
```

アプリケーション全体でこのイベントをリッスン可能:

```javascript
window.addEventListener('strum', function(event) {
    const velocity = event.detail.velocity;
    // 音声再生や視覚的フィードバック
});
```

## プライバシー配慮

### データ処理ポリシー

1. **即時破棄**: カメラ映像は処理後に即座に破棄
2. **サーバー送信なし**: すべての処理はクライアントサイドで完結
3. **保存なし**: 画像データや動画データの保存は行わない
4. **LED通知**: カメラアクティブ時にインジケーターを点灯

### 実装

```javascript
onResults(results) {
    // プライバシー: 画像データは即座に破棄され、保存されない
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];
        // 処理のみを行い、画像データは保存しない
    }
}
```

## UIコンポーネント

### HTML構造

```html
<div class="camera-gesture">
    <h2>カメラでストローク</h2>

    <div class="camera-controls">
        <button id="enable-camera-btn">カメラを有効化</button>
        <button id="disable-camera-btn">カメラを無効化</button>
    </div>

    <div class="camera-status">
        <div id="camera-indicator" class="camera-indicator">
            <span class="indicator-dot"></span>
            <span class="indicator-text">カメラ: オフ</span>
        </div>
    </div>

    <div class="camera-preview">
        <video id="camera-video" class="camera-video" playsinline></video>
    </div>

    <div class="camera-instructions">
        <p>カメラの前に手をかざし、下に動かしてストロークしてください</p>
    </div>
</div>
```

### スタイル

- **インジケーター**: カメラ状態を視覚的に表示
- **アニメーション**: アクティブ時にパルスアニメーション
- **レスポンシブ**: モバイル対応レイアウト

## テスト

### テストファイル

`/Users/taguchireo/camp/python/air_guitar_02/static/js/tests/camera.test.js`

### テストケース

1. **コンストラクタ**: 正しい初期化を確認
2. **isStrumming**: ストローク検出ロジックを検証
3. **strumVelocity**: 速度計算を検証
4. **triggerNote**: イベント発火を確認
5. **カメラ操作**: 開始/停止を検証
6. **プライバシー**: データ保存がないことを確認

### テスト実行

```bash
# テストランナーをブラウザで開く
open static/js/tests/camera.test.html
```

## デモページ

### URL

`/static/js/tests/camera-demo.html`

### 機能

1. カメラの有効化/無効化
2. ストローク検出のリアルタイム表示
3. ストロークログの記録
4. Velocity値の表示

## パフォーマンス

### 最適化

- **解像度**: 640x480（精度と速度のバランス）
- **検出遅延**: 目標100ms以内
- **CPU使用率**: モデル複雑さ1で最適化

### ブラウザ対応

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## トラブルシューティング

### カメラが起動しない

1. **権限確認**: ブラウザのカメラ権限を確認
2. **HTTPS確認**: カメラアクセスにはHTTPSが必要（localhost除く）
3. **デバイス確認**: 他のアプリでカメラが使用されていないか確認

### ストロークが検出されない

1. **照明条件**: 十分な照明を確保
2. **手の位置**: カメラの前に手を正しく配置
3. **閾値調整**: `STRUM_THRESHOLD`値を調整（デフォルト: 0.05）

### パフォーマンス問題

1. **解像度低下**: 320x240に変更
2. **モデル複雑さ**: 0に変更（より高速だが精度低下）
3. **検出手数**: 1に変更（デフォルト）

## 今後の改善

1. **マルチハンド対応**: 複数の手の同時検出
2. **高度なジェスチャー**: スライド、ハンマリング等の検出
3. **キャリブレーション**: ユーザーに合わせた閾値調整
4. **学習機能**: ユーザーの演奏スタイルに適応

## 関連ドキュメント

- [design.md](../../design.md) - MediaPipe統合詳細
- [task.md](../../task.md) - タスク1.12の詳細
- [requirements.md](../../requirements.md) - 要件10の詳細

## 作成者

- Sub-Agent-4 (MediaPipe & Camera Specialist)
- 作成日: 2026-01-27

## ライセンス

この実装はVirtuTuneプロジェクトの一部です。
