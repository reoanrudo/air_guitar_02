/**
 * PC Player
 *
 * Air Guitar ProのPCプレイヤー実装
 *
 * 機能:
 * - カメラハンドトラッキング（TensorFlow.js Handpose）
 * - リズムゲーム（ノーツ生成・移動・判定）
 * - ストローク検知（速度ベース・ゾーンクロス）
 * - スコア/コンボシステム
 * - Canvasレンダリング
 * - WebRTC受信とフレット状態更新
 * - パーティクルエフェクト
 * - オーディオエンジン統合
 */

class PCPlayer {
  constructor(videoElement, canvasElement) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');

    // ゲーム状態
    this.isReady = false;
    this.isAudioStarted = false;
    this.isPlaying = false;
    this.isPaused = false;

    // スコア・コンボ
    this.scoreDisplay = 0;
    this.comboDisplay = 0;
    this.lastRating = null;

    this.scoreRef = 0;
    this.comboRef = 0;

    // リズムゲーム
    this.fretStatesRef = [0, 0, 0, 0, 0, 0];
    this.notesRef = [];
    this.nextNoteId = 0;
    this.lastNoteSpawnTime = 0;
    this.isAudioStartedRef = false;

    // ストローク検知
    this.lastYRef = null;
    this.isStrummingRef = false;
    this.lastStrumTimeRef = 0;

    // パーティクル
    this.particlesRef = [];
    this.frameIdRef = null;

    // WebRTC・オーディオ
    this.webrtc = null;
    this.audioEngine = null;
    this.particleSystem = null;
    this.roomId = '';

    // 定数
    this.CANVAS_W = window.innerWidth;
    this.CANVAS_H = window.innerHeight;
    this.NOTE_SPEED = 16;
    this.HIT_ZONE_X = this.CANVAS_W - 250;
    this.HIT_WINDOW = 120;
    this.STRUM_VELOCITY_THRESHOLD = 18;

    // ストロークゾーン
    this.STRUM_ZONE = {
      x: this.CANVAS_W - 650,
      y: this.CANVAS_H * 0.65,
      w: 600,
      h: this.CANVAS_H * 0.3
    };
    this.STRUM_MID_Y = this.STRUM_ZONE.y + (this.STRUM_ZONE.h / 2);

    // 可能なフレット
    this.POSSIBLE_FRETS = [0, 3, 5, 7, 10, 12];
  }

  async initialize(roomId) {
    console.log(`PCPlayer: Initializing with room ID: ${roomId}`);

    this.roomId = roomId;

    // カメラセットアップ
    await this.setupCamera();

    // TensorFlow.js初期化
    await this.setupHandposeModel();

    // WebRTC・オーディオ・パーティクル初期化
    this.webrtc = new WebRTCService(roomId);
    this.audioEngine = new AudioEnginePro();
    this.particleSystem = new ParticleSystem();

    // WebRTCイベントリスナー設定
    this.webrtc.onMessage((data) => {
      if (data.type === 'FRET_UPDATE') {
        this.fretStatesRef = data.payload;
        console.log('PCPlayer: Fret states updated:', data.payload);
      }
    });

    this.webrtc.onConnected(() => {
      console.log('PCPlayer: Connected to mobile controller');
      this.updateConnectionStatus(true);
    });

    // リサイズハンドラー
    this.handleResize();

    // ゲームループ開始
    this.gameLoop();

    this.isReady = true;
  }

  async setupCamera() {
    console.log('PCPlayer: Setting up camera...');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: 1280,
          height: 720,
          frameRate: { ideal: 60 }
        },
        audio: false
      });

      if (this.video.srcObject) {
        URL.revokeObjectURL(this.video.srcObject);
      }
      this.video.srcObject = stream;

      this.video.onloadedmetadata = async () => {
        await this.video.play();
        console.log('PCPlayer: Camera ready, starting game loop...');
        this.gameLoop();
      };
    } catch (error) {
      console.error('PCPlayer: Camera setup failed:', error);
      alert('カメラの起動に失敗しました。\nエラー: ' + error.message);
    }
  }

  async setupHandposeModel() {
    console.log('PCPlayer: Loading Handpose model...');

    try {
      await tf.setBackend('webgl');
      await tf.ready();
      this.handposeModel = await handpose.load();

      console.log('PCPlayer: Handpose model loaded');
    } catch (error) {
      console.error('PCPlayer: Handpose model failed:', error);
      alert('AIモデルのロードに失敗しました。\nエラー: ' + error.message);
    }
  }

  gameLoop() {
    if (!this.isPlaying) return;

    requestAnimationFrame(() => this.gameLoop());
  }

  gameLoop() {
    // ハンドトラッキングとストローク検知
    const predictions = await this.detectHands();

    // ストローク判定
    const strumResult = this.detectStrum(predictions);

    // ノーツ更新
    this.updateNotes();

    // パーティクル更新
    this.particleSystem.update();

    // Canvas描画
    this.render(predictions, strumResult);

    this.frameIdRef = requestAnimationFrame(() => this.gameLoop());
  }

  async detectHands() {
    try {
      const predictions = await this.handposeModel.estimateHands(this.video, {
        flipHorizontal: true
      });

      if (predictions.length === 0) {
        return { hasHands: false };
      }

      // 顔の誤検知防止フィルタ（画面下半分のみ）
      const vScale = this.CANVAS_H / this.video.videoHeight;
      const validHands = predictions.filter(p => {
        const wristY = p.landmarks[0][1] * vScale;
        return wristY > this.CANVAS_H * 0.45;
      });

      if (validHands.length > 0) {
        // 最も右側の手（右利き用）を選択
        const hand = validHands.reduce((prev, curr) => {
          return prev.landmarks[0][0] < curr.landmarks[0][0] ? prev : curr;
        });

        return {
          hasHands: true,
          hand: hand,
          avgTipY: (hand.landmarks[8][1] + hand.landmarks[12][1] + hand.landmarks[16][1]) / 3 * vScale,
          handX: this.CANVAS_W - (hand.landmarks[0][0] * vScale)
        };
      }

      return { hasHands: false };
    } catch (error) {
      console.error('PCPlayer: Hand detection failed:', error);
      return { hasHands: false };
    }
  }

  detectStrum(predictions) {
    if (!predictions.hasHands) {
      if (this.lastYRef !== null) {
        this.isStrummingRef = false;
      this.lastYRef = null;
      }
      return { didStrum: false, handX: null };
    }

    const hand = predictions.hand;
    const displayHandX = this.CANVAS_W - hand.handX;

    // ゾーン内チェック
    if (displayHandX > this.STRUM_ZONE.x &&
        displayHandX < this.STRUM_ZONE.x + this.STRUM_ZONE.w &&
        hand.avgTipY > this.STRUM_ZONE.y &&
        hand.avgTipY < this.STRUM_ZONE.y + this.STRUM_ZONE.h) {

      if (this.lastYRef !== null) {
        const vel = hand.avgTipY - this.lastYRef;
        const speed = Math.abs(vel);
        const now = Date.now();

        // 中央判定線を跨いだ瞬間のみ「ストローク」として認める
        const crossed = (this.lastYRef < this.STRUM_MID_Y && hand.avgTipY >= this.STRUM_MID_Y) ||
                        (this.lastYRef > this.STRUM_MID_Y && hand.avgTipY <= this.STRUM_MID_Y);

        if (crossed && speed > this.STRUM_VELOCITY_THRESHOLD) {
          if (now - this.lastStrumTimeRef > 150) {
            this.isStrummingRef = true;
            this.lastStrumTimeRef = now;
            this.lastYRef = hand.avgTipY;
            
            // パーティクル発生（ストローク時）
            for (let i = 0; i < 15; i++) {
              this.particleSystem.emit(displayHandX, hand.avgTipY, '#f97316');
            }
            
            // 音再生
            if (this.isAudioStartedRef) {
              this.audioEngine.playStrum(this.fretStatesRef, 'down');
            }
            
            // ヒット判定
            this.checkHit(note);
            
            return { didStrum: true, handX };
          }
        }
      }

      this.lastYRef = hand.avgTipY;

      // ゾーン外の場合
      if (displayHandX <= this.STRUM_ZONE.x || displayHandX >= this.STRUM_ZONE.x + this.STRUM_ZONE.w ||
          hand.avgTipY <= this.STRUM_ZONE.y || hand.avgTipY >= this.STRUM_ZONE.y + this.STRUM_ZONE.h) {
        this.isStrummingRef = false;
        this.lastYRef = null;
      }
    }

    return { didStrum: false, handX: null };
  }

  spawnNote() {
    const now = Date.now();
    if (now - this.lastNoteSpawnTime > 1100) {
      const note = {
        id: this.nextNoteId++,
        x: -100,
        fret: this.POSSIBLE_FRETS[Math.floor(Math.random() * this.POSSIBLE_FRETS.length)],
        hit: false,
        missed: false
      };

      this.notesRef.push(note);
      this.lastNoteSpawnTime = now;

      console.log(`PCPlayer: Spawned note ${note.id} at fret ${note.fret}`);
    }
  }

  updateNotes() {
    const notes = this.notesRef;
    const now = Date.now();

    for (let i = notes.length - 1; i >= 0; i--) {
      const note = notes[i];

      if (!note.hit && !note.missed) {
        note.x += this.NOTE_SPEED;

        // ミス判定
        if (note.x > this.HIT_ZONE_X + this.HIT_WINDOW) {
          note.missed = true;
          this.handleMiss();
        }
      }
    }

    this.notesRef = notes.filter(n => !n.hit && !n.missed);
  }

  checkHit(note) {
    const now = Date.now();
    const dist = Math.abs(note.x - this.HIT_ZONE_X);

    if (dist < this.HIT_WINDOW / 3.5) {
      // PERFECT
      this.scoreRef += 1000;
      this.comboRef += 1;
      this.showRating('PERFECT', 'text-yellow-400');
      
      for (let i = 0; i < 20; i++) {
        this.particleSystem.emit(this.HIT_ZONE_X, this.CANVAS_H * 0.5, '#fbbf24');
      }
    } else if (dist < this.HIT_WINDOW) {
      // GREAT
      this.scoreRef += 500;
      this.comboRef += 1;
      this.showRating('GREAT', 'text-sky-400');
      
      for (let i = 0; i < 15; i++) {
        this.particleSystem.emit(this.HIT_ZONE_X, this.CANVAS_H * 0.5, '#38bdf8');
      }
    } else {
      // MISS
      this.comboRef = 0;
      this.showRating('MISS', 'text-red-500');
      this.audioEngine.playMuted();
    }

    this.updateUI();
  }

  handleMiss() {
    console.log(`PCPlayer: Miss! Combo reset to 0`);
    this.showRating('MISS', 'text-red-500');
  }

  showRating(text, color) {
    this.lastRating = { text, color };
    
    const display = document.getElementById('judgement-display');
    if (display) {
      display.textContent = text;
      display.className = `absolute top-[40%] left-1/2 -translate-x-1/2 -translate-y-1/2 text-[16rem] font-black italic z-40 animate-ping opacity-0 ${color}`;
      
      setTimeout(() => {
        display.classList.remove('show');
      }, 500);
    }
  }

  updateUI() {
    // スコア
    const scoreDisplay = document.getElementById('score-display');
    if (scoreDisplay) {
      scoreDisplay.textContent = this.scoreRef.toLocaleString();
    }

    // コンボ
    const comboDisplay = document.getElementById('combo-display');
    if (comboDisplay) {
      comboDisplay.textContent = this.comboRef;
    }
    
    // 評当性による色変更
    const comboContainer = document.getElementById('combo-container');
    if (comboContainer && this.comboRef > 5) {
      comboContainer.classList.remove('hidden');
    } else if (comboContainer) {
      comboContainer.classList.add('hidden');
    }
  }

  updateConnectionStatus(connected) {
    const dot = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-status');
    const roomCodeDisplay = document.getElementById('room-id-display');

    if (connected) {
      dot.classList.remove('bg-red-500', 'animate-pulse');
      dot.classList.add('bg-green-500', 'shadow-[0_0_12px_rgba(34,197,94,0.6)]');
      text.textContent = 'Linked';
      text.classList.remove('text-white', 'opacity-70');
      text.classList.add('text-green-400');
    } else {
      dot.classList.remove('bg-green-500');
      dot.classList.add('bg-red-500', 'animate-pulse');
      text.textContent = 'Linking...';
      text.classList.remove('text-green-400');
      text.classList.add('text-white', 'opacity-70');
    }
  }

  render(predictions, strumResult) {
    const w = this.CANVAS_W;
    const h = this.CANVAS_H;

    // Canvasクリア
    this.ctx.fillStyle = '#020617';
    this.ctx.fillRect(0, 0, w, h);

    // ビデオ描画（ミラーモード）
    this.ctx.save();
    this.ctx.globalAlpha = 0.25;
    this.ctx.scale(-1, 1);
    this.ctx.drawImage(this.video, 0, 0, w, h);
    this.ctx.restore();

    // 弦描画
    this.renderStrings();

    // ノーツ描画
    this.renderNotes();

    // ハンドメッシュ描画
    if (strumResult.handX) {
      this.renderHandMesh(predictions.hand, strumResult.didStrum);
    }

    // パーティクル描画
    this.particleSystem.draw(this.ctx);

    // UI更新
    this.renderUI();
  }

  renderStrings() {
    const frets = this.fretStatesRef;
    const stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];

    for (let i = 0; i < 6; i++) {
      const yOff = i * 30;
      const active = frets[i] > 0;

      this.ctx.strokeStyle = active ? '#fb923c' : 'rgba(255, 255, 255, 0.1)';
      this.ctx.lineWidth = active ? 8 : 2;
      this.ctx.beginPath();
      this.ctx.moveTo(0, this.STRUM_ZONE.y + yOff);
      this.ctx.lineTo(w, this.STRUM_ZONE.y + yOff + 140);
      this.ctx.stroke();
    }
  }

  renderNotes() {
    const centerY = this.STRUM_ZONE.y + (this.STRUM_ZONE.h / 2);

    this.notesRef.forEach(note => {
      if (!note.hit && !note.missed) {
        // ノーツの色
        const gradient = this.ctx.createRadialGradient(
          note.x - 55,
          centerY - 45,
          0,
          note.x - 55,
          centerY + 45,
          40
        );
        gradient.addColorStop(0, '#f97316');
        gradient.addColorStop(1, '#fb923c');

        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.roundRect(note.x - 55, centerY - 45, 110, 90, 20);

        this.ctx.fillStyle = '#fff';
        this.ctx.font = '900 44px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(`F${note.fret}`, note.x, centerY + 25);
      }
    });
  }

  renderHandMesh(landmarks, isStrumming) {
    const vScale = this.CANVAS_H / this.video.videoHeight;
    const hScale = this.CANVAS_W / this.video.videoWidth;

    const fingers = [
      [0, 1, 2, 3, 4],    // Thumb
      [0, 5, 6, 7, 8],    // Index
      [0, 9, 10, 11, 12],  // Middle
      [0, 13, 14, 15, 16],  // Ring
      [0, 17, 18, 19, 20]   // Pinky
    ];

    this.ctx.strokeStyle = isStrumming ? '#fb923c' : '#0ea5e9';
    this.ctx.lineWidth = 3;
    this.ctx.shadowBlur = isStrumming ? 30 : 5;
    this.ctx.shadowColor = isStrumming ? '#fb923c' : '#0ea5e9';

    this.ctx.save();
    this.ctx.scale(-1, 1);
    this.ctx.translate(-this.CANVAS_W, 0);

    // 指ごとのラインを描画
    fingers.forEach(fingerIdxs => {
      this.ctx.beginPath();
      fingerIdxs.forEach((idx, i) => {
        const [x, y] = landmarks[fingerIdx[i]];
        this.ctx.lineTo(x * hScale, y * vScale);
      });
      this.ctx.stroke();
    });

    this.ctx.restore();
  }

  renderUI() {
    // スコア更新
    const scoreDisplay = document.getElementById('score-display');
    if (scoreDisplay) {
      scoreDisplay.textContent = this.scoreRef.toLocaleString();
    }

    // コンボ更新
    const comboDisplay = document.getElementById('combo-display');
    if (comboDisplay) {
      comboDisplay.textContent = this.comboRef;
    }
  }

  async startGame() {
    console.log('PCPlayer: Starting game...');

    // オーディオ開始
    await this.audioEngine.start();
    this.isAudioStartedRef = true;

    // ゲーム開始
    this.isPlaying = true;
    this.isPaused = false;

    // UI更新
    const loadingOverlay = document.getElementById('loading-overlay');
    const startOverlay = document.getElementById('start-overlay');

    if (loadingOverlay) {
      loadingOverlay.classList.add('hidden');
    }

    if (startOverlay) {
      startOverlay.classList.add('hidden');
    }
  }

  pauseGame() {
    this.isPaused = !this.isPaused;
  }

  stopGame() {
    console.log('PCPlayer: Stopping game...');
    this.isPlaying = false;
    this.isPaused = false;

    this.isAudioStartedRef = false;

    // UIリセット
    this.scoreRef = 0;
    this.comboRef = 0;
    this.updateUI();

    // フレームIDをリセット
    if (this.frameIdRef) {
      cancelAnimationFrame(this.frameIdRef);
      this.frameIdRef = null;
    }
  }

  handleResize() {
    this.CANVAS_W = window.innerWidth;
    this.CANVAS_H = window.innerHeight;

    // Canvasサイズ更新
    this.canvas.width = this.CANVAS_W;
    this.canvas.height = this.CANVAS_H;

    this.STRUM_ZONE.x = this.CANVAS_W - 650;
    this.STRUM_ZONE.y = this.CANVAS_H * 0.65;
    this.STRUM_ZONE.w = 600;
    this.STRUM_ZONE.h = this.CANVAS_H * 0.3;
    this.STRUM_MID_Y = this.STRUM_ZONE.y + (this.STRUM_ZONE.h / 2);
    this.HIT_ZONE_X = this.CANVAS_W - 250;

    console.log(`PCPlayer: Resized to ${this.CANVAS_W}x${this.CANVAS_H}`);
  }

  exit() {
    console.log('PCPlayer: Exit button pressed');

    // ゲーム停止
    this.stopGame();

    // ページ遷移
    window.location.href = '/air-guitar-pro/';
  }
}

// グローバルインスタンスを作成
let pcPlayer;

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
  console.log('PCPlayer: DOM loaded, initializing...');

  // Canvas要素を取得
  const videoElement = document.getElementById('video-element');
  const canvasElement = document.getElementById('canvas-element');

  if (!videoElement || !canvasElement) {
    console.error('PCPlayer: Required elements not found');
    alert('必要な要素が見つかりません');
    return;
  }

  // URLパラメータからルームIDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const roomId = urlParams.get('room');

  console.log(`PCPlayer: Initializing with room ID: ${roomId}`);

  // PCプレイヤーインスタンスを作成
  pcPlayer = new PCPlayer(videoElement, canvasElement);

  // WebRTC初期化（ホストモード）
  pcPlayer.initialize(roomId);

  // 初期化後にルームコードを表示
  const roomCodeDisplay = document.getElementById('room-id-display');
  if (roomCodeDisplay) {
    roomCodeDisplay.textContent = roomId;
  }

  console.log('PCPlayer: Initialization complete');
});
