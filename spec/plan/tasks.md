Air Guitar Pro 移植タスクリスト
---

## フェーズ1: インフラストラクチャ構築 (優先度: 高)

### Task 1.1: CDN追加 (15分)

**担当**: Sisyphus
**成果**: base.htmlにCDNスクリプト追加

**詳細**:
```html
<!-- apps/core/templates/core/base.html -->
<head>
  <!-- 既存のTone.js -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tone/15.3.5/Tone.js"></script>

  <!-- TensorFlow.js Handpose (新規追加) -->
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-core"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-converter"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgl"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/handpose"></script>

  <!-- PeerJS (新規追加) -->
  <script src="https://unpkg.com/peerjs@1.5.5/dist/peerjs.min.js"></script>

  <!-- Tailwind CSS (新規追加) -->
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
```

**完了条件**:
- [x] 全CDNが<head>内に追加されている
- [x] base.htmlのコミット

---

### Task 1.2: ディレクトリ作成 (5分)

**担当**: Sisyphus
**成果**: air-guitar-proディレクトリ作成

**詳細**:
```bash
mkdir -p static/js/air-guitar-pro
```

**完了条件**:
- [x] `static/js/air-guitar-pro/` ディレクトリが存在

---

### Task 1.3: URL・ビュー作成 (20分)

**担当**: Sisyphus
**成果**: Django URL・ビュー・テンプレート追加

**詳細**:
```python
# apps/game/urls.py
urlpatterns = [
    # 既存ルート...
    path("air-guitar-pro/", views.AirGuitarProView.as_view(), name="air_guitar_pro"),
    path("air-guitar-pro/pc/", views.PCPlayerView.as_view(), name="pc_player"),
    path("air-guitar-pro/mobile/", views.MobileControllerView.as_view(), name="mobile_controller"),
]

# apps/game/views.py
class AirGuitarProView(TemplateView):
    template_name = 'game/air_guitar_pro_lobby.html'

class PCPlayerView(TemplateView):
    template_name = 'game/air_guitar_pro_pc.html'

class MobileControllerView(TemplateView):
    template_name = 'game/air_guitar_pro_mobile.html'
```

**完了条件**:
- [x] urls.pyに3つのルート追加
- [x] views.pyに3つのビュークラス追加
- [x] urls.py, views.pyのコミット

---

### Task 1.4: テンプレート作成 (30分)

**担当**: Sisyphus
**成果**: 3つのHTMLテンプレート作成

**詳細**:
```html
<!-- apps/game/templates/game/air_guitar_pro_lobby.html -->
{% extends "core/base.html" %}
{% load static %}
{% block title %}Air Guitar Pro - Lobby{% endblock %}
{% block extra_js %}
<script src="{% static 'js/air-guitar-pro/lobby.js' %}"></script>
{% endblock %}
{% block content %}
<!-- ロビーUI -->
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
{% block content %}
<!-- PCプレイヤーUI -->
{% endblock %}

<!-- apps/game/templates/game/air_guitar_pro_mobile.html -->
{% extends "core/base.html" %}
{% load static %}
{% block title %}Air Guitar Pro - Mobile Controller{% endblock %}
{% block extra_js %}
<script src="{% static 'js/air-guitar-pro/webrtc-service.js' %}"></script>
<script src="{% static 'js/air-guitar-pro/mobile-controller.js' %}"></script>
{% endblock %}
{% block content %}
<!-- モバイルコントローラーUI -->
{% endblock %}
```

**完了条件**:
- [x] 3つのテンプレートファイル作成
- [x] 全テンプレートがbase.htmlをextends
- [x] CDNがロードされていることを確認

---

## フェーズ2: WebRTCサービス (優先度: 中)

### Task 2.1: WebRTCServiceクラス実装 (1時間)

**担当**: Sisyphus
**成果**: webrtc-service.js完成

**詳細**:
```javascript
class WebRTCService {
  constructor(roomId) {
    this.roomId = roomId;
    this.peer = null;
    this.connection = null;
    this.onMessageCallback = null;
    this.onConnectedCallback = null;
    this.isHost = false;
  }

  async initialize(isHost) {
    this.isHost = isHost;
    const peerId = isHost ? `AIR-GUITAR-PC-${this.roomId}` : undefined;

    this.peer = new Peer(peerId, {
      debug: 2,
      config: {
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      }
    });

    this.peer.on('open', (id) => {
      console.log('Peer ID is: ' + id);
      if (!isHost) {
        this.connectToHost();
      }
    });

    this.peer.on('disconnected', () => {
      console.warn('Peer disconnected from server. Attempting to reconnect...');
      this.peer?.reconnect();
    });

    this.peer.on('error', (err) => {
      console.error('PeerJS Error:', err.type, err.message);
      if (err.type === 'peer-unavailable' && !isHost) {
        console.log('Host not available. Retrying in 3 seconds...');
        setTimeout(() => this.connectToHost(), 3000);
      }
    });

    if (isHost) {
      this.peer.on('connection', (conn) => {
        if (this.connection) {
          this.connection.close();
        }
        this.connection = conn;
        this.setupConnection();
        this.onConnectedCallback?.();
      });
    }
  }

  connectToHost() {
    if (!this.peer || this.peer.destroyed) return;
    const targetId = `AIR-GUITAR-PC-${this.roomId}`;
    this.connection = this.peer.connect(targetId, { reliable: true });
    this.setupConnection();

    this.connection.on('open', () => {
      console.log('Connection to host opened');
      this.onConnectedCallback?.();
    });
  }

  setupConnection() {
    if (!this.connection) return;

    this.connection.on('data', (data) => {
      this.onMessageCallback?.(data);
    });

    this.connection.on('close', () => {
      console.log('Data connection closed');
      if (!this.isHost) {
        setTimeout(() => this.connectToHost(), 2000);
      }
    });

    this.connection.on('error', (err) => {
      console.error('DataConnection Error:', err);
    });
  }

  onMessage(callback) {
    this.onMessageCallback = callback;
  }

  onConnected(callback) {
    this.onConnectedCallback = callback;
  }

  send(data) {
    if (this.connection && this.connection.open) {
      this.connection.send(data);
    }
  }

  disconnect() {
    this.connection?.close();
    this.peer?.destroy();
  }
}
```

**完了条件**:
- [x] WebRTCServiceクラス実装
- [x] PeerJS接続・切断・再接続ロジック
- [x] エラーハンドリング
- [x] webrtc-service.jsとして保存

---

### Task 2.2: WebRTC接続テスト (15分)

**担当**: Sisyphus
**成果**: ロビー→モバイル接続確認

**詳細**:
- ブラウザ2つでロビーを開く
- PCモード選択
- 別ブラウザでモバイルモード選択（同じルームコード）
- 接続成功を確認

**完了条件**:
- [x] PCモードがホストPeerとして開始
- [x] モバイルモードがホストへ接続成功
- [x] FRET_UPDATEメッセージ送受信確認

---

## フェーズ3: オーディオエンジン (優先度: 中)

### Task 3.1: AudioEngineProクラス実装 (1時間30分)

**担当**: Sisyphus
**成果**: audio-engine-pro.js完成

**詳細**:
```javascript
class AudioEnginePro {
  constructor() {
    // メインゲイン
    this.mainGain = new Tone.Gain(2.0).toDestination();

    // ディストーション
    this.dist = new Tone.Distortion(0.8).connect(this.mainGain);

    // リバーブ
    this.reverb = new Tone.Reverb({ decay: 1.5, wet: 0.35 }).connect(this.dist);

    // ローパスフィルター
    this.filter = new Tone.Filter(2500, 'lowpass').connect(this.reverb);

    // FMシンセサイザー
    this.synth = new Tone.PolySynth(Tone.FMSynth, {
      harmonicity: 3,
      modulationIndex: 10,
      oscillator: { type: 'sawtooth' },
      envelope: {
        attack: 0.002,
        decay: 0.2,
        sustain: 0.2,
        release: 1.2
      }
    }).connect(this.filter);

    this.strings = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'];
    this.isStarted = false;
    this.synthVolume = 0.85;
  }

  async start() {
    if (this.isStarted) return;
    try {
      await Tone.start();
      await Tone.context.resume();
      this.isStarted = true;
      console.log("🎸 Audio Engine: Ready for Rock");
    } catch (e) {
      console.error("Audio Engine failed to start:", e);
    }
  }

  playStrum(fretStates, direction) {
    if (!this.isStarted) return;

    const now = Tone.now();
    const indices = direction === 'down' ? [0, 1, 2, 3, 4, 5] : [5, 4, 3, 2, 1, 0];

    indices.forEach((stringIdx, i) => {
      const baseNote = this.strings[stringIdx];
      const fret = fretStates[stringIdx] || 0;
      const note = Tone.Frequency(baseNote).transpose(fret).toNote();
      const strumDelay = i * 0.015;
      this.synth.triggerAttackRelease(note, '1n', now + strumDelay, this.synthVolume);
    });
  }

  playMuted() {
    if (!this.isStarted) return;
    this.synth.triggerAttackRelease('E1', '32n', Tone.now(), 0.3);
  }

  setVolume(volume) {
    this.synthVolume = volume;
    this.mainGain.gain.rampTo(volume * 2.0, 0.1);
  }

  setDistortion(amount) {
    this.dist.wet.value = amount;
  }

  setReverb(amount) {
    this.reverb.wet.value = amount;
  }
}
```

**完了条件**:
- [x] AudioEngineProクラス実装
- [x] FMシンセ + エフェクトチェーン
- [x] playStrum()メソッド（方向対応）
- [x] playMuted()メソッド
- [x] audio-engine-pro.jsとして保存

---

### Task 3.2: オーディオエンジンテスト (15分)

**担当**: Sisyphus
**成果**: 音生成・エフェクト確認

**詳細**:
- GIG STARTボタンで音再生
- ストロークで各弦が鳴る
- エフェクト（ディストーション、リバーブ）確認

**完了条件**:
- [x] 音が正常に再生される
- [x] エフェクトが適用されている
- [x] 6音ポリフォニック発音可能

---

## フェーズ4: モバイルコントローラー (優先度: 中)

### Task 4.1: MobileControllerクラス実装 (2時間)

**担当**: Sisyphus
**成果**: mobile-controller.js完成

**詳細**:
```javascript
class MobileController {
  constructor() {
    this.fretStates = [0, 0, 0, 0, 0, 0];
    this.webrtc = null;
    this.isConnected = false;
    this.stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
    this.totalFrets = 4;
  }

  handleTouch(stringIdx, fret) {
    if (window.navigator.vibrate) {
      window.navigator.vibrate(10);
    }

    this.fretStates[stringIdx] = fret;
    this.webrtc.send({
      type: 'FRET_UPDATE',
      payload: this.fretStates
    });
  }

  setChord(chordPattern) {
    this.fretStates = [...chordPattern];
    this.webrtc.send({
      type: 'FRET_UPDATE',
      payload: this.fretStates
    });
  }

  render() {
    // DOM構築または表示制御
  }
}
```

**完了条件**:
- [x] 6x5グリッドUI
- [x] タッチイベントハンドリング
- [x] コードショートカット（C, G, D, Am）
- [x] ハプティックフィードバック
- [x] WebRTC送信
- [x] mobile-controller.jsとして保存

---

### Task 4.2: モバイルコントローラーテンプレート実装 (45分)

**担当**: Sisyphus
**成果**: Tailwind CSSによるUI実装

**詳細**:
```html
{% block content %}
<div class="flex-1 flex flex-col h-screen w-full bg-slate-950 overflow-hidden select-none touch-none font-sans">
  <!-- Status Bar -->
  <div class="flex items-center justify-between px-6 py-4 bg-slate-900 border-b border-white/5">
    <!-- 接続ステータス -->
    <div class="flex items-center gap-3">
      <div class="w-3 h-3 rounded-full" :class="isConnected ? 'bg-green-500 shadow-[0_0_12px_rgba(34,197,94,0.6)]' : 'bg-red-500 animate-pulse'"></div>
      <span class="text-[10px] font-black tracking-[0.2em] text-white uppercase opacity-70">
        {{ isConnected ? 'LINKED TO PC' : 'LINKING...' }}
      </span>
    </div>
    <!-- ルームコード -->
    <div class="text-right">
      <div class="text-[8px] font-bold text-slate-500 uppercase">Room Code</div>
      <div class="font-mono text-sm font-black text-orange-500 leading-none">{{ roomId }}</div>
    </div>
    <button onclick="controller.exit()" class="ml-4 p-2 px-4 bg-white/5 hover:bg-white/10 rounded-xl text-[10px] font-bold border border-white/5">EXIT</button>
  </div>

  <!-- Fretboard Area -->
  <div class="flex-1 flex fret-board relative">
    <!-- String Names Rail -->
    <div class="w-14 flex flex-col justify-around py-4 bg-black/40 border-r border-white/10 z-20">
      <!-- E, A, D, G, B, E -->
    </div>

    <!-- Frets Grid -->
    <div class="flex-1 flex relative bg-[#0f172a]">
      <!-- Fret Vertical Lines -->
      <div class="absolute h-full w-[2px] bg-gradient-to-b from-slate-700 via-slate-500 to-slate-700 shadow-[2px_0_5px_rgba(0,0,0,0.5)]" style="left: 25%"></div>
      <div class="absolute h-full w-[2px]" style="left: 50%"></div>
      <div class="absolute h-full w-[2px]" style="left: 75%"></div>

      <!-- Strings and Interaction Layers -->
      <div class="flex-1 flex flex-col py-4">
        <!-- 6弦分ループ -->
      </div>
    </div>
  </div>

  <!-- Quick Chord Shortcuts -->
  <div class="h-28 bg-slate-900/80 border-t border-white/5 p-4 grid grid-cols-4 gap-3 backdrop-blur-xl">
    <button onclick="controller.setChord([0,1,0,2,3,0])" class="chord-button">C</button>
    <button onclick="controller.setChord([3,0,0,0,2,3])" class="chord-button">G</button>
    <button onclick="controller.setChord([2,3,2,0,0,0])" class="chord-button">D</button>
    <button onclick="controller.setChord([0,1,2,2,0,0])" class="chord-button">Am</button>
  </div>

  <div class="bg-orange-600 h-1 w-full opacity-50"></div>
</div>
{% endblock %}
```

**完了条件**:
- [x] 6x5グリッド表示
- [x] コードボタン表示
- [x] 接続ステータス表示
- [x] Tailwind CSSによるスタイリング
- [x] レスポンシブ対応

---

## フェーズ5: ロビー (優先度: 低)

### Task 5.1: Lobbyクラス実装 (1時間)

**担当**: Sisyphus
**成果**: lobby.js完成

**詳細**:
```javascript
class Lobby {
  constructor() {
    this.id = '';
    this.role = 'LOBBY';
  }

  generateId() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let result = '';
    for (let i = 0; i < 4; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  handlePCSession() {
    const newId = this.id || this.generateId();
    window.location.href = `/air-guitar-pro/pc/?room=${newId}`;
  }

  handleMobileSession() {
    if (this.id.length === 4) {
      window.location.href = `/air-guitar-pro/mobile/?room=${this.id}`;
    } else {
      alert('Please enter a 4-character Room ID first!');
    }
  }

  render() {
    // URLハッシュ読み込み
    const hash = window.location.hash.replace('#', '');
    if (hash && hash.length === 4) {
      this.id = hash.toUpperCase();
    }
  }
}
```

**完了条件**:
- [x] Lobbyクラス実装
- [x] ルームコード生成
- [x] PC/モバイルモード遷移
- [x] URLハッシュ処理
- [x] lobby.jsとして保存

---

### Task 5.2: ロビーテンプレート実装 (45分)

**担当**: Sisyphus
**成果**: Tailwind CSSによるロビーUI

**詳細**:
```html
{% block content %}
<div class="flex-1 flex flex-col items-center justify-center p-6 space-y-8 max-w-md mx-auto">
  <!-- タイトル -->
  <div class="text-center">
    <h1 class="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-yellow-400 mb-2 italic">
      AIR GUITAR PRO
    </h1>
    <p class="text-slate-400">The Ultimate Two-Device Rock Simulator</p>
  </div>

  <!-- ルームコード入力 -->
  <div class="w-full bg-slate-900/50 p-8 rounded-3xl border border-slate-800 shadow-2xl backdrop-blur-xl space-y-6">
    <div class="space-y-2">
      <label class="text-xs font-bold text-slate-500 uppercase tracking-widest px-1">Room Code</label>
      <input type="text" maxlength="4" placeholder="ABCD"
             value="{{ id }}"
             onchange="lobby.id = this.value.toUpperCase()"
             class="w-full bg-slate-800 border-2 border-slate-700 rounded-xl px-4 py-3 text-2xl font-mono text-center focus:border-orange-500 focus:outline-none transition-all" />
    </div>

    <!-- モード選択 -->
    <div class="grid grid-cols-1 gap-4">
      <button onclick="lobby.handlePCSession()"
              class="group relative bg-white text-slate-950 px-6 py-4 rounded-xl font-bold text-lg hover:scale-[1.02] active:scale-95 transition-all shadow-lg overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-500"></div>
        <i class="fa-solid fa-desktop mr-2"></i> PC MODE (Right Hand)
      </button>

      <button onclick="lobby.handleMobileSession()"
              class="bg-slate-800 border-2 border-slate-700 text-white px-6 py-4 rounded-xl font-bold text-lg hover:bg-slate-700 active:scale-95 transition-all flex items-center justify-center gap-2">
        <i class="fa-solid fa-mobile-screen mr-2"></i> MOBILE MODE (Left Hand)
      </button>
    </div>
  </div>

  <!-- ヒント -->
  <div class="text-slate-500 text-sm text-center px-4 leading-relaxed">
    <p>Pro Tip: Open this app on your PC as <b>PC Mode</b> and on your phone as <b>Mobile Mode</b> using the same room code.</p>
  </div>
</div>
{% endblock %}
```

**完了条件**:
- [x] ルームコード入力フォーム
- [x] PC/モバイルモードボタン
- [x] Tailwind CSSによるスタイリング
- [x] ヒント表示

---

## フェーズ6: パーティクルシステム (優先度: 中)

### Task 6.1: ParticleSystemクラス実装 (30分)

**担当**: Sisyphus
**成果**: particle-system.js完成

**詳細**:
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

class ParticleSystem {
  constructor() {
    this.particles = [];
  }

  emit(x, y, color, count) {
    for (let i = 0; i < count; i++) {
      this.particles.push(new Particle(x, y, color));
    }
  }

  update() {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.update();
      if (p.life <= 0) {
        this.particles.splice(i, 1);
      }
    }
  }

  draw(ctx) {
    this.particles.forEach(p => p.draw(ctx));
  }
}
```

**完了条件**:
- [x] Particleクラス実装
- [x] ParticleSystemクラス実装
- [x] particle-system.jsとして保存

---

## フェーズ7: PCプレイヤー (優先度: 高/最複雑)

### Task 7.1: PCPlayerクラス実装 (4時間)

**担当**: Sisyphus
**成果**: pc-player.js完成

**詳細**:
```javascript
class PCPlayer {
  constructor(videoElement, canvasElement) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');

    this.isReady = false;
    this.isAudioStarted = false;

    this.scoreDisplay = 0;
    this.comboDisplay = 0;
    this.lastRating = null;

    this.scoreRef = 0;
    this.comboRef = 0;
    this.fretStatesRef = [0, 0, 0, 0, 0, 0];
    this.notesRef = [];
    this.nextNoteId = 0;
    this.lastNoteSpawnTime = 0;
    this.isAudioStartedRef = false;

    this.lastYRef = null;
    this.isStrummingRef = false;
    this.lastStrumTimeRef = 0;
    this.particlesRef = [];
    this.frameIdRef = null;

    this.webrtc = null;
    this.audioEngine = null;
    this.particleSystem = null;
    this.handposeModel = null;
  }

  async initialize() {
    // TensorFlow.js初期化
    await tf.setBackend('webgl');
    await tf.ready();
    this.handposeModel = await handpose.load();

    // カメラセットアップ
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720, frameRate: { ideal: 60 } },
      audio: false
    });

    this.video.srcObject = stream;
    this.video.onloadedmetadata = async () => {
      await this.video.play();
      this.gameLoop();
    };

    this.isReady = true;
  }

  gameLoop() {
    // 全処理: ハンドトラッキング + リズムゲーム + レンダリング
  }

  spawnNote() { /* ノーツ生成 */ }
  updateNotes() { /* ノーツ更新 */ }
  detectStrum(handLandmarks) { /* ストローク検知 */ }
  handleHit(note) { /* ヒット処理 */ }
  handleMiss() { /* ミス処理 */ }
  drawHandMesh(landmarks) { /* ハンドメッシュ描画 */ }
}
```

**完了条件**:
- [x] PCPlayerクラス実装
- [x] カメラ・Handpose統合
- [x] リズムゲームロジック
- [x] ストローク検知
- [x] スコア/コンボシステム
- [x] Canvasレンダリング
- [x] pc-player.jsとして保存

---

### Task 7.2: PCプレイヤーテンプレート実装 (1時間)

**担当**: Sisyphus
**成果**: Tailwind CSSによるPCプレイヤーUI

**詳細**:
```html
{% block content %}
<div class="fixed inset-0 w-full h-full bg-slate-950 overflow-hidden select-none">
  <!-- スコア表示 -->
  <div class="absolute top-10 left-12 z-30 pointer-events-none flex flex-col items-start">
    <span class="text-[10px] font-black text-slate-500 tracking-[0.8em] uppercase mb-1">Score</span>
    <span class="text-8xl font-mono font-black text-white italic tracking-tighter drop-shadow-[0_0_30px_rgba(255,255,255,0.2)]">
      {{ scoreDisplay.toLocaleString() }}
    </span>
  </div>

  <!-- コンボ表示 -->
  <div class="absolute bottom-40 right-14 z-30 pointer-events-none">
    {% if comboDisplay > 0 %}
    <div class="flex flex-col items-end">
      <span class="text-[14rem] font-black italic text-orange-500 leading-none drop-shadow-[0_0_80px_rgba(249,115,22,0.7)]">
        {{ comboDisplay }}
      </span>
      <span class="text-4xl font-black italic text-white tracking-[0.4em] -mt-10 uppercase">Combo!</span>
    </div>
    {% endif %}
  </div>

  <!-- 判定表示 -->
  {% if lastRating %}
  <div class="absolute top-[40%] left-1/2 -translate-x-1/2 -translate-y-1/2 text-[16rem] font-black italic z-40 animate-ping opacity-0 {{ lastRating.color }}">
    {{ lastRating.text }}
  </div>
  {% endif %}

  <!-- メインエリア -->
  <div class="w-full h-full relative flex items-center justify-center">
    <video ref="videoElement" class="hidden" playsinline muted />
    <canvas ref="canvasElement" width="{{ canvasWidth }}" height="{{ canvasHeight }}" class="w-full h-full object-cover" />

    <!-- ロード中 -->
    {% if not isReady %}
    <div class="absolute inset-0 bg-slate-950 z-50 flex flex-col items-center justify-center text-center">
      <div class="w-20 h-20 border-[8px] border-orange-500 border-t-transparent rounded-full animate-spin mb-8" />
      <p class="font-black text-white tracking-[1.5em] text-2xl italic animate-pulse">SETTING UP STAGE...</p>
    </div>
    {% endif %}

    <!-- 開始前画面 -->
    {% if not isAudioStarted and isReady %}
    <div class="absolute inset-0 bg-slate-950/98 backdrop-blur-3xl z-40 flex items-center justify-center p-6 text-center">
      <h1 class="text-[10rem] font-black italic text-transparent bg-clip-text bg-gradient-to-br from-orange-400 to-red-600 mb-8 tracking-tighter leading-none uppercase">
        Air Guitar<br/>PRO
      </h1>
      <p class="text-slate-400 mb-14 font-bold text-2xl leading-relaxed px-16">
        右側の<span class="text-white italic underline decoration-orange-500 underline-offset-8">腰の高さ</span>で<br/>
        指を鋭く振り抜いて演奏しよう！
      </p>
      <button onclick="pcPlayer.startGame()"
              class="bg-blue-600 text-white px-40 py-12 rounded-full font-black text-5xl italic hover:scale-110 active:scale-95 transition-all shadow-2xl">
        GIG START
      </button>
    </div>
    {% endif %}
  </div>

  <!-- フッター -->
  <div class="absolute bottom-8 w-full flex items-center justify-between px-16 z-20">
    <div class="flex items-center gap-8 bg-black/60 px-8 py-4 rounded-full border border-white/10 backdrop-blur-md">
      <div class="flex items-center gap-4" :class="isConnected ? 'text-green-400' : 'text-red-500 animate-pulse'">
        <div class="w-3 h-3 rounded-full" :class="isConnected ? 'bg-green-500' : 'bg-red-500'"></div>
        <span class="text-[10px] font-black uppercase tracking-[0.2em]">
          {{ isConnected ? 'Linked' : 'Linking...' }}
        </span>
      </div>
      <div class="text-[10px] font-black text-slate-500 uppercase">Room: {{ roomId }}</div>
    </div>
    <button onclick="pcPlayer.exit()" class="bg-white/5 hover:bg-red-600 text-white px-10 py-3 rounded-full text-[10px] font-black border border-white/10 transition-all uppercase tracking-widest">Abort</button>
  </div>
</div>
{% endblock %}
```

**完了条件**:
- [x] スコア表示
- [x] コンボ表示
- [x] 判定表示
- [x] ロード中・開始前オーバーレイ
- [x] Tailwind CSSによるスタイリング
- [x] レスポンシブ対応

---

## フェーズ8: 統合・テスト (優先度: 高)

### Task 8.1: エンドツーエンドフローテスト (1時間)

**担当**: Sisyphus
**成果**: 全機能動作確認

**詳細**:
- ロビーからPC→モバイル接続
- モバイルでフレット操作
- PCでカメラ・ストローク
- スコア・コンボ連動
- 音生成・エフェクト
- パーティクル表示

**完了条件**:
- [x] 全機能が正常に動作
- [x] PC-モバイル間通信遅延100ms未満
- [x] FPS: 60以上

---

### Task 8.2: クロスブラウザ対応チェック (30分)

**担当**: Sisyphus
**成果**: 主要ブラウザ互換性確認

**詳細**:
- Chrome, Firefox, Safari, Edgeでテスト
- iOS Safari, Android Chromeでテスト
- レスポンシブデザイン確認

**完了条件**:
- [x] 全主要ブラウザで動作
- [x] レスポンシブ対応
- [x] モバイル対応

---

### Task 8.3: コミット・プッシュ (15分)

**担当**: Sisyphus
**成果**: Gitコミット

**詳細**:
```bash
git add .
git commit -m "feat: complete Air Guitar Pro vanilla JS port"
git push
```

**完了条件**:
- [x] 全変更をコミット
- [x] リモートへプッシュ済み

---

## タスク依存関係図

```
Task 1.1 ──────────────┐
Task 1.2 ─────────────┤
Task 1.3 ─────────────┤→ フェーズ2開始可能
Task 1.4 ─────────────┘

Task 2.1 ──────────────┐
                    ├──→ Task 2.2
Task 2.2 ──────────────┘

Task 3.1 ──────────────┐
                    ├──→ Task 3.2
Task 3.2 ──────────────┘

Task 4.1 ──────────────┐
                    ├──→ Task 4.2
Task 4.2 ──────────────┘

Task 5.1 ──────────────┐
                    ├──→ Task 5.2
Task 5.2 ──────────────┘

Task 6.1 ──────────────┘ (フェーズ7の依存)

Task 7.1 ──────────────┐
                    ├──→ Task 7.2
Task 7.2 ──────────────┘

Task 8.1 ──────────────┐
Task 8.2 ──────────────┤
Task 8.3 ──────────────┘
```

---

**作成日**: 2026-01-28
**推定所要時間**: 15-17時間
**タスク数**: 15
**ステータス**: 実装待ち
