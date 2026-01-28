Air Guitar Pro (React/TypeScript)の完全再現 - 移植計画

---

## コンテキスト

### ソース: Air Guitar Pro
場所: `/Users/taguchireo/camp/python/air_guitar_02/air-guitar-pro/`

### ターゲット: Django統合
場所: `/Users/taguchireo/camp/python/air_guitar_02/`

### 技術的制約
- 純粋なJavaScriptを使用（React、TypeScript、JSXなし）
- Djangoテンプレートシステムに統合
- ビルド不要の静的ファイルとして実装
- Air Guitar Proの全機能を保持

---

## 1. 要件分析

### 機能要件 (FR)

#### 1.1 ロビー (Lobby.tsx)
- [x] ルームコード入力（4文字、自動生成オプション）
- [x] PCモード選択ボタン
- [x] モバイルコントローラーモード選択ボタン
- [x] URLハッシュからのルームコード自動読み込み

#### 1.2 PCプレイヤー (PCPlayer.tsx)
- [x] カメラハンドトラッキング（TensorFlow.js Handpose）
- [x] リズムゲーム（右から左へスクロールするノーツ）
- [x] ストローク検知（速度ベース、ゾーンクロス判定）
- [x] スコア/コンボシステム（PERFECT/GREAT/MISS判定）
- [x] パーティクルエフェクト（ヒット時）
- [x] Canvasレンダリング（ビデオオーバーレイ）
- [x] 接続ステータス表示（Linking.../Linked）
- [x] ルームID表示
- [x] Exitボタン
- [x] ロード中アニメーション
- [x] 開始前画面（GIG STARTボタン）

#### 1.3 モバイルコントローラー (MobileController.tsx)
- [x] 6弦 x 5フレットグリッド（オープン弦 + 4フレット）
- [x] クイックコードショートカット（C, G, D, Am）
- [x] タッチフィードバック（navigator.vibrate）
- [x] 弦名表示（E, A, D, G, B, E）
- [x] 選択弦のハイライト
- [x] 接続ステータス表示
- [x] ルームコード表示
- [x] Exitボタン

#### 1.4 WebRTCサービス (WebRTCService.ts)
- [x] PeerJS P2P通信
- [x] ホスト/クライアントモード
- [x] 接続時コールバック
- [x] データ受信コールバック
- [x] データ送信
- [x] エラーハンドリング（peer-unavailable, network）
- [x] 自動再接続
- [x] 切断処理

#### 1.5 オーディオエンジン (AudioEngine.ts)
- [x] Tone.js FMシンセサイザー
- [x] ディストーション効果
- [x] リバーブ効果
- [x] ローパスフィルター
- [x] ポリフォニックシンセ（6音同時発音）
- [x] ストローク方向による弦の順序変化
- [x] ミュート音
- [x] 音量制御

### 非機能要件 (NFR)
- [x] パフォーマンス: 60FPS以上
- [x] レイテンシー: WebRTC通信遅延最小化
- [x] 互換性: モダンブラウザ対応
- [x] ユーザビリティ: 直感的なUI/UX
- [x] セキュリティ: HTTPS対応、CSRF対策

---

## 2. ファイル構造

### 新規作成ファイル

```
static/js/
├── air-guitar-pro/
│   ├── lobby.js          # ロビー画面制御
│   ├── pc-player.js       # PCプレイヤー（カメラ + ゲーム）
│   ├── mobile-controller.js # モバイルコントローラー
│   ├── webrtc-service.js  # WebRTC通信サービス
│   ├── particle-system.js # パーティクルシステム
│   └── audio-engine-pro.js # オーディオエンジン（高機能版）
```

### 既存ファイル（拡張）

```
static/js/
├── audio-engine.js       # 既存 - Tone.jsロード済み
└── game.js              # 既存 - WebSocketベースゲーム
```

---

## 3. コンポーネントマッピング

### React → Vanilla JavaScript

#### 3.1 App.tsx → HTMLページ構造
- `useState` → グローバル変数/クラスプロパティ
- `useEffect` → DOMContentLoadedイベントリスナー
- 条件レンダリング → DOMの表示/非表示切り替え

#### 3.2 Lobby.tsx → Lobbyクラス
```javascript
class Lobby {
  constructor() {
    this.roomId = '';
    this.role = 'LOBBY';
  }

  generateRoomId() { /* 4文字コード生成 */ }
  handlePCMode() { /* PCモード開始 */ }
  handleMobileMode() { /* モバイルモード開始 */ }
  render() { /* DOM構築または表示制御 */ }
}
```

#### 3.3 PCPlayer.tsx → PCPlayerクラス
```javascript
class PCPlayer {
  constructor(videoElement, canvasElement) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.score = 0;
    this.combo = 0;
    this.notes = [];
    this.particles = [];
    this.isReady = false;
    this.isAudioStarted = false;
    this.fretStates = [0, 0, 0, 0, 0, 0];
    this.lastY = null;
    this.isStrumming = false;
  }

  async initialize() {
    // カメラセットアップ
    // TensorFlow.jsモデルロード
    // WebRTC接続
    // オーディオ初期化
  }

  async gameLoop() {
    // ハンドトラッキング
    // ノーツ更新
    // ストローク検知
    // パーティクル更新
    // Canvas描画
  }

  detectStrum(handLandmarks) { /* 速度ベース検知 */ }
  spawnNote() { /* ノーツ生成 */ }
  updateNotes() { /* ノーツ更新 */ }
  handleHit(note) { /* ヒット処理 */ }
  handleMiss() { /* ミス処理 */ }
  drawHandMesh(landmarks) { /* ハンドメッシュ描画 */ }
}
```

#### 3.4 MobileController.tsx → MobileControllerクラス
```javascript
class MobileController {
  constructor() {
    this.fretStates = [0, 0, 0, 0, 0, 0];
    this.webrtc = null;
    this.isConnected = false;
    this.stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
  }

  handleTouch(stringIndex, fret) {
    // フレット状態更新
    // ハプティックフィードバック
    // WebRTCで送信
  }

  setChord(chordPattern) {
    // コード一括設定
  }

  render() { /* DOM構築または表示制御 */ }
}
```

#### 3.5 WebRTCService.ts → WebRTCServiceクラス
```javascript
class WebRTCService {
  constructor(roomId) {
    this.roomId = roomId;
    this.peer = null;
    this.connection = null;
    this.onMessageCallback = null;
    this.onConnectedCallback = null;
  }

  async initialize(isHost) {
    // PeerJS初期化
    // 接続確立
  }

  send(data) {
    // データ送信
  }

  onMessage(callback) {
    // 受信コールバック設定
  }

  disconnect() {
    // 接続切断
  }
}
```

---

## 4. 依存ライブラリ管理

### CDN追加 (base.htmlへ追記)

```html
<!-- TensorFlow.js Handpose -->
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-core"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-converter"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgl"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/handpose"></script>

<!-- PeerJS -->
<script src="https://unpkg.com/peerjs@1.5.5/dist/peerjs.min.js"></script>

<!-- Tone.js (既存) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/15.3.5/Tone.js"></script>

<!-- Tailwind CSS (Styling用) -->
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
```

---

## 5. Django統合ポイント

### 5.1 URLルーティング

```python
# apps/game/urls.py
urlpatterns = [
    # 既存ルート...
    path("air-guitar-pro/", views.AirGuitarProView.as_view(), name="air_guitar_pro"),
    path("air-guitar-pro/pc/", views.PCPlayerView.as_view(), name="pc_player"),
    path("air-guitar-pro/mobile/", views.MobileControllerView.as_view(), name="mobile_controller"),
]
```

### 5.2 ビュー

```python
# apps/game/views.py

class AirGuitarProView(TemplateView):
    template_name = 'game/air_guitar_pro_lobby.html'

class PCPlayerView(TemplateView):
    template_name = 'game/air_guitar_pro_pc.html'

class MobileControllerView(TemplateView):
    template_name = 'game/air_guitar_pro_mobile.html'
```

### 5.3 テンプレート構成

```html
<!-- apps/game/templates/game/air_guitar_pro_lobby.html -->
{% extends "core/base.html" %}
{% load static %}
{% block title %}Air Guitar Pro - Lobby{% endblock %}

{% block extra_js %}
<script src="{% static 'js/air-guitar-pro/lobby.js' %}"></script>
{% endblock %}

<!-- apps/game/templates/game/air_guitar_pro_pc.html -->
{% extends "core/base.html" %}
{% load static %}
{% block title %}Air Guitar Pro - PC Player{% endblock %}

{% block extra_js %}
<script src="{% static 'js/air-guitar-pro/webrtc-service.js' %}"></script>
<script src="{% static 'js/air-guitar-pro/particle-system.js' %}"></script>
<script src="{% static 'js/air-guitar-pro/audio-engine-pro.js' %}"></script>
<script src="{% static 'js/air-guitar-pro/pc-player.js' %}"></script>
{% endblock %}

<!-- apps/game/templates/game/air_guitar_pro_mobile.html -->
{% extends "core/base.html" %}
{% load static %}
{% block title %}Air Guitar Pro - Mobile Controller{% endblock %}

{% block extra_js %}
<script src="{% static 'js/air-guitar-pro/webrtc-service.js' %}"></script>
<script src="{% static 'js/air-guitar-pro/mobile-controller.js' %}"></script>
{% endblock %}
```

---

## 6. 実装順序

### フェーズ1: インフラストラクチャ (優先度高)
1. **依存ライブラリCDN追加**
   - base.htmlにTensorFlow.js, PeerJS CDNを追加
   - Tailwind CSSのCDNを追加

2. **ディレクトリ作成**
   - `static/js/air-guitar-pro/` ディレクトリ作成

3. **URL・ビュー・テンプレート作成**
   - urls.pyにルート追加
   - views.pyにビュー追加
   - テンプレートファイル作成

### フェーズ2: WebRTCサービス (中優先度)
4. **webrtc-service.js実装**
   - PeerJSラップクラス
   - 接続管理
   - エラーハンドリング
   - 自動再接続ロジック

5. **WebRTCサービステスト**
   - ロビーからモバイル接続テスト

### フェーズ3: オーディオエンジン (中優先度)
6. **audio-engine-pro.js実装**
   - FMシンセサイザー作成
   - エフェクトチェーン構築
   - ストロークメソッド実装

7. **オーディオエンジンテスト**
   - 音生成テスト
   - エフェクト確認

### フェーズ4: モバイルコントローラー (中優先度)
8. **mobile-controller.js実装**
   - 6x5グリッドUI
   - タッチイベントハンドリング
   - コードショートカット実装
   - WebRTC統合

9. **モバイルコントローラーテンプレート実装**
   - Tailwind CSSによるスタイリング
   - レスポンシブデザイン

### フェーズ5: ロビー (低優先度)
10. **lobby.js実装**
    - ルームコード生成
    - モード選択UI
    - URLハッシュ処理

11. **ロビーテンプレート実装**
    - 入力フォーム
    - ボタンUI

### フェーズ6: PCプレイヤー (高優先度/最複雑)
12. **particle-system.js実装**
    - パーティクルクラス
    - 更新/描画メソッド

13. **pc-player.js実装**
    - カメラ初期化
    - TensorFlow.js Handpose統合
    - リズムゲームロジック
    - スコア/コンボシステム
    - ストローク検知アルゴリズム
    - Canvasレンダリング

14. **PCプレイヤーテンプレート実装**
    - ビデオ要素（非表示）
    - Canvas要素
    - スコア/コンボ表示
    - UIオーバーレイ

### フェーズ7: 統合・テスト (重要)
15. **WebRTC通信テスト**
    - PC-モバイル間通信確認
    - 遅延測定

16. **統合テスト**
    - エンドツーエンドゲームフロー確認
    - パフォーマンス測定
    - 各ブラウザ互換性確認

---

## 7. 技術仕様詳細

### 7.1 WebRTCメッセージプロトコル

```javascript
// フレット更新（モバイル→PC）
{
  type: 'FRET_UPDATE',
  payload: [0, 3, 0, 2, 0, 0] // 各弦のフレット
}

// 準備完了（任意）
{
  type: 'READY',
  payload: {}
}
```

### 7.2 ストローク検知アルゴリズム

```javascript
// 速度閾値
const STRUM_VELOCITY_THRESHOLD = 18;

// ゾーン定義
const STRUM_ZONE = {
  x: CANVAS_W - 650,
  y: CANVAS_H * 0.65,
  w: 600,
  h: CANVAS_H * 0.3
};

// 判定ライン
const STRUM_MID_Y = STRUM_ZONE.y + (STRUM_ZONE.h / 2);

// クロス判定
const crossed = (lastY < STRUM_MID_Y && currentY >= STRUM_MID_Y) ||
                (lastY > STRUM_MID_Y && currentY <= STRUM_MID_Y);

if (crossed && speed > STRUM_VELOCITY_THRESHOLD) {
  // ストローク検出
}
```

### 7.3 ノーツ生成パターン

```javascript
// ノーツ生成タイミング
const NOTE_SPAWN_INTERVAL = 1100; // ms

// ノーツ速度
const NOTE_SPEED = 16; // ピクセル/フレーム

// ヒットゾーン位置
const HIT_ZONE_X = CANVAS_W - 250;

// 判定ウインドウ
const HIT_WINDOW = 120;

// 可能なフレット
const POSSIBLE_FRETS = [0, 3, 5, 7, 10, 12];
```

### 7.4 パーティクルシステム

```javascript
class Particle {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.vx = (Math.random() - 0.5) * 35;
    this.vy = (Math.random() - 0.5) * 35;
    this.life = 1.0;
    this.color = color;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.life -= 0.04;
  }

  draw(ctx) {
    ctx.globalAlpha = this.life;
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, 8 * this.life, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1.0;
  }
}
```

### 7.5 TensorFlow.js使用パターン

```javascript
// バックエンド設定
await tf.setBackend('webgl');
await tf.ready();

// モデルロード
const model = await handpose.load();

// ビデオストリーム取得
const stream = await navigator.mediaDevices.getUserMedia({
  video: { width: 1280, height: 720, frameRate: { ideal: 60 } },
  audio: false
});

// ハンド推論
const predictions = await model.estimateHands(video, {
  flipHorizontal: true // ミラーモード
});

// 顔誤検知防止
const validHands = predictions.filter(p => {
  const wristY = p.landmarks[0][1] * vScale;
  return wristY > CANVAS_H * 0.45; // 画面下半分のみ有効
});
```

---

## 8. 成功基準

### 機能的完成度
- [ ] ロビーでルームコード生成・選択可能
- [ ] PCモードでカメラハンドトラッキング動作
- [ ] PCモードでリズムゲームプレイ可能
- [ ] モバイルコントローラーでタッチ操作可能
- [ ] PC-モバイル間WebRTC通信成功
- [ ] スコア/コンボシステム正常動作
- [ ] パーティクルエフェクト表示
- [ ] 全判定（PERFECT/GREAT/MISS）正常
- [ ] オーディオエンジンによるギター音生成

### 品質基準
- [ ] FPS: 60以上
- [ ] レイテンシ: 100ms未満
- [ ] クロスブラウザ対応: Chrome, Firefox, Safari, Edge
- [ ] モバイル対応: iOS, Android

### ユーザビリティ
- [ ] 直感的なUI
- [ ] レスポンシブデザイン
- [ ] タッチ操作のレスポンス（50ms未満）
- [ ] 適切なフィードバック

---

## 9. リスク・課題

### 技術的リスク
1. **TensorFlow.jsロード時間**: 初回ロードに数秒かかる可能性
   - 対策: ローディング画面追加

2. **カメラ許可**: ブラウザのカメラ許可が必要
   - 対策: エラーメッセージ追加

3. **WebRTC NAT越え**: 一部ネットワーク環境で接続失敗
   - 対策: STUNサーバー使用、エラーハンドリング

4. **オーディオコンテキスト**: ユーザー操作が必要
   - 対策: "GIG START"ボタン設置

### 開発スケジュール
- フェーズ1-2: 1-2時間
- フェーズ3-4: 2-3時間
- フェーズ5-6: 3-4時間
- フェーズ7: 1-2時間
- **合計**: 7-11時間

---

**作成日**: 2026-01-28
**バージョン**: 1.0
**ステータス**: 計画完了、実装待ち
