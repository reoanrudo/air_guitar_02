Air Guitar Pro 移植設計書
---

## アーキテクチャ概要

### システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                   Django Backend                      │
│                                                      │
│  ┌────────────────────────────────────────────┐          │
│  │          URL Routing                   │          │
│  │  /air-guitar-pro/  → Lobby View     │          │
│  │  /air-guitar-pro/pc/  → PC View      │          │
│  │  /air-guitar-pro/mobile/ → Mobile View  │          │
│  └────────────────────────────────────────────┘          │
│                      │                               │
│                      ▼                               │
│              ┌──────────────┐                         │
│              │   Templates    │                         │
│              └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend (Vanilla JS)                   │
│                                                      │
│  ┌─────────────┐  ┌──────────────────┐            │
│  │   Lobby    │  │   WebRTCService  │            │
│  └─────────────┘  └──────────────────┘            │
│         │                   │                    │
│         ▼                   ▼                    │
│  ┌─────────────┐  ┌──────────────────┐            │
│  │ PC Player   │  │ Mobile Controller│            │
│  └─────────────┘  └──────────────────┘            │
│         │                   │                    │
│         └─────────┬───────────┘            │
│                   ▼                           │
│  ┌────────────────────────────┐               │
│  │   WebRTC (PeerJS)        │               │
│  └────────────────────────────┘               │
│                   │                           │
│                   ▼                           │
│         P2P Communication                  │
│                                                      │
│  ┌────────────────────────────┐               │
│  │   External Services        │               │
│  │  - TensorFlow.js Handpose  │               │
│  │  - Tone.js FM Synth       │               │
│  │  - Camera API            │               │
│  └────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## コンポーネント設計

### 1. WebRTCServiceクラス

**役割**: P2P通信を管理する中間層

**責任**:
- PeerJS接続の初期化・管理
- データ送信・受信のラップ
- エラーハンドリング・再接続ロジック
- コネクション状態の管理

**インタフェース**:

```javascript
class WebRTCService {
  constructor(roomId);
  async initialize(isHost);
  send(data);
  onMessage(callback);
  onConnected(callback);
  disconnect();
}
```

**メッセージプロトコル**:

```javascript
// FRET_UPDATE: モバイル→PC
{
  type: 'FRET_UPDATE',
  payload: [0, 3, 0, 2, 0, 0] // 各弦のフレット
}

// READY: 初期化完了通知（任意）
{
  type: 'READY',
  payload: {}
}
```

**状態遷移**:
```
[未接続] → [初期化中] → [接続確立] → [通信中] → [切断]
    ↑            ↓              ↓             ↓         ↓
    └──────────再接続───────────┘
```

### 2. AudioEngineProクラス

**役割**: Tone.jsによるギター音生成

**責任**:
- FMシンセサイザーの設定
- エフェクトチェーンの構築（Distortion → Reverb → Filter）
- ストローク方向による弦の順序制御
- 音量・エフェクトパラメータの調整

**エフェクトチェーン**:
```
Input → PolySynth(FM) → Filter(Lowpass) → Reverb → Distortion → Gain → Output
```

**インタフェース**:

```javascript
class AudioEnginePro {
  constructor();
  async start();
  playStrum(fretStates, direction); // 'up' or 'down'
  playMuted();
  setVolume(volume);
  setDistortion(amount);
  setReverb(amount);
}
```

**パラメータ**:
- `strings`: ['E2', 'A2', 'D3', 'G3', 'B3', 'E4']
- `harmonicity`: 3
- `modulationIndex`: 10
- `distortion`: 0.8
- `reverb.decay`: 1.5s
- `reverb.wet`: 0.35
- `filter.frequency`: 2500Hz (lowpass)
- `strumDelay`: 15ms per string

### 3. ParticleSystemクラス

**役割**: 視覚エフェクトの管理

**責任**:
- パーティクルの生成・更新・描画
- パーティクルの寿命管理
- パフォーマンス最適化

**パーティクル構造**:

```javascript
class Particle {
  x, y;        // 位置
  vx, vy;      // 速度ベクトル
  life;         // 寿命 (1.0 → 0.0)
  color;        // 色
}
```

**描画パイプライン**:
```
生成 → 更新(移動・減衰) → 描画 → 寿命チェック → 破棄
```

### 4. PCPlayerクラス

**役割**: PC用メインゲームロジック

**責任**:
- カメラアクセス・ビデオストリーム管理
- TensorFlow.js Handposeによる手の検知
- ストローク検知アルゴリズム
- リズムゲームロジック（ノーツ生成・更新・判定）
- スコア/コンボシステム
- Canvasレンダリング（ビデオ + UI + パーティクル）
- WebRTC通信の受信

**サブシステム**:
1. **HandTrackingSystem**
   - カメラ初期化
   - Handpose推論
   - 顔誤検知フィルタ

2. **RhythmGameSystem**
   - ノーツスポーン
   - ノーツ移動・更新
   - ヒット判定（タイミングウィンドウ）
   - ミス判定

3. **StrumDetectionSystem**
   - 速度計算
   - ゾーン内チェック
   - 判定ラインクロス検知

4. **ScoreSystem**
   - スコア計算
   - コンボ管理
   - 判定ラベル表示

5. **RenderingSystem**
   - Canvas描画
   - ビデオオーバーレイ
   - ハンドメッシュ描画
   - パーティクル描画

**状態遷移**:
```
[初期化中] → [ロード中] → [準備完了] → [プレイ中] → [一時停止] → [終了]
                           ↓              ↓            ↓          ↓
                    [接続待ち] ←────────────────────┘          └→[初期化中]
```

### 5. MobileControllerクラス

**役割**: モバイル用コントローラーUI

**責任**:
- 6x5グリッドUIの描画
- タッチイベントハンドリング
- フレット状態管理
- WebRTCデータ送信
- ハプティックフィードバック
- クイックコード設定

**グリッド構造**:
```
         Open   F1   F2   F3   F4
    E  [O]    [1]   [2]   [3]   [4]
    A  [O]    [1]   [2]   [3]   [4]
    D  [O]    [1]   [2]   [3]   [4]
    G  [O]    [1]   [2]   [3]   [4]
    B  [O]    [1]   [2]   [3]   [4]
    E  [O]    [1]   [2]   [3]   [4]
```

**インタラクション**:
- タッチ: フレット選択 + WebRTC送信 + 振動
- コードボタン: 一括フレット設定

### 6. Lobbyクラス

**役割**: モード選択UI

**責任**:
- ルームコード生成（4文字大文字英数字）
- URLハッシュからのルームコード読み込み
- モード選択（PC/モバイル）
- ルームコード表示

---

## データフロー設計

### モバイル→PC 通信フロー

```
[モバイル]
    タッチイベント
        ↓
    フレット状態更新
        ↓
    WebRTC送信: {type: 'FRET_UPDATE', payload: fretStates}
        ↓
    [ネットワーク: PeerJS P2P]
        ↓
[PC]
    WebRTC受信
        ↓
    fretStatesRef更新
        ↓
    弦表示更新
```

### PCメインループ

```
[requestAnimationFrame]
        ↓
[HandTracking]
    ビデオフレーム取得
        ↓
    Handpose推論
        ↓
    顔フィルタリング
        ↓
    手座標取得
        ↓
    ストローク検知
        ↓
    速度計算・クロス判定
        ↓
[判定: ストローク発生?]
    YES → 音再生・スコア更新・パーティクル生成
    NO  → スキップ
        ↓
[RhythmGame]
    ノーツスポーン（定期）
        ↓
    ノーツ更新（速度で移動）
        ↓
    ヒット判定（距離チェック）
        ↓
    HIT → スコア加算・コンボ増加・音再生・パーティクル
    MISS → コンボリセット・ミュート音
        ↓
[Rendering]
    Canvasクリア
        ↓
    ビデオ描画（アルファ0.25）
        ↓
    弦描画
        ↓
    ノーツ描画
        ↓
    ハンドメッシュ描画
        ↓
    パーティクル描画
        ↓
    UI描画（スコア・コンボ・判定）
        ↓
[requestAnimationFrame] ← 繰り返し
```

---

## レスポンシブデザイン戦略

### CSSフレームワーク
- **使用**: Tailwind CSS (CDN)
- **理由**: Reactのクラス名をそのまま利用可能

### レスポンシブ対応

```css
/* Mobile Controller */
@media (max-width: 768px) {
  .fret-grid { font-size: 1rem; }
  .chord-button { padding: 0.75rem; }
}

/* PC Player */
@media (min-width: 769px) {
  .game-container { width: 100vw; }
  canvas { width: 100%; }
}
```

### タッチ最適化

```javascript
// viewportメタタグ
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

// タッチアクション制御
.fret-board {
  touch-action: none; // スクロール・ズーム無効化
}
```

---

## エラーハンドリング戦略

### WebRTCエラー

| エラータイプ | 原因 | 対策 |
|--------------|------|--------|
| peer-unavailable | 対向先が存在しない | 自動再接続（3秒間隔） |
| network | ネットワーク切断 | peer.reconnect()（5秒後） |
| browser-incompatible | WebRTC未対応ブラウザ | ユーザー通知 |
| invalid-id | 無効なPeerID | 再生成・再接続 |

### カメラエラー

| エラータイプ | 対策 |
|--------------|--------|
| NotAllowedError | ユーザーがカメラ許可拒否 | エラーメッセージ表示 |
| NotFoundError | カメラデバイス未検出 | ガイダンス表示 |
| NotReadableError | カメラアクセス不可 | 再試行ボタン提供 |

### TensorFlow.jsエラー

| エラータイプ | 対策 |
|--------------|--------|
| モデルロード失敗 | CDNフォールバック |
| 推論タイムアウト | フレームスキップ |

---

## パフォーマンス最適化

### TensorFlow.js最適化

```javascript
// バックエンド設定
await tf.setBackend('webgl'); // GPUアクセラレーション

// モデルロードオプション
const model = await handpose.load({
  maxContinuousChecks: Infinity, // 不要なバウンディングボックス検知無効化
  detectionConfidence: 0.8,    // 信頼度閾値
});
```

### Canvas最適化

```javascript
// ビデオ描画最適化
ctx.globalAlpha = 0.25; // 不透明度低減

// パーティクルオブジェクトプール
const particlePool = [];
const MAX_PARTICLES = 100;

// ガベージコレクション
requestAnimationFrame(() => {
  // メインループ
});
```

### WebRTC最適化

```javascript
// バッファリング
const sendBuffer = [];
const SEND_INTERVAL = 50; // ms

setInterval(() => {
  if (sendBuffer.length > 0) {
    conn.send(sendBuffer);
    sendBuffer = [];
  }
}, SEND_INTERVAL);
```

---

## セキュリティ設計

### WebRTCセキュリティ

```javascript
// STUNサーバー（Google公共サーバー）
config: {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
}
```

### クロスオリジン対策

```javascript
// CSPヘッダー（Django settings.py）
CSP_DEFAULT_SRC = "'self'"
CSP_SCRIPT_SRC = "'self' cdn.jsdelivr.net cdnjs.cloudflare.com unpkg.com cdn.tailwindcss.com"

// HTTPS強制（本番環境）
SECURE_SSL_REDIRECT = True
```

---

## デバッグ戦略

### ログレベル

```javascript
// PeerJSデバッグモード
const peer = new Peer({
  debug: 2, // 0=none, 1=errors, 2=warnings, 3=all
});

// カスタムロガー
const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  error: (...args) => console.error('[ERROR]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args)
};
```

### 可視化デバッグ

```javascript
// 開発モードフラグ
const DEBUG = window.location.search.includes('debug=true');

if (DEBUG) {
  // 判定ゾーン描画
  ctx.strokeStyle = 'yellow';
  ctx.strokeRect(STRUM_ZONE.x, STRUM_ZONE.y, STRUM_ZONE.w, STRUM_ZONE.h);

  // ランドマーク描画
  landmarks.forEach(([x, y], i) => {
    ctx.fillStyle = 'red';
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
  });
}
```

---

## 依存関係図

```
base.html (CDNロード)
    ↓
lobby.js ←───── WebRTCService
    ↓
mobile-controller.js ← WebRTCService
    ↓
pc-player.js ← WebRTCService
    ├─→ AudioEnginePro
    ├─→ ParticleSystem
    └─→ TensorFlow.js Handpose
```

---

**作成日**: 2026-01-28
**バージョン**: 1.0
**ステータス**: 設計完了
