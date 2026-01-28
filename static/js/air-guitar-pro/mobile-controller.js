/**
 * Mobile Controller
 *
 * Air Guitar ProのモバイルコントローラーUI
 *
 * 機能:
 * - 6弦 x 5フレットグリッド
 * - タッチイベントハンドリング
 * - WebRTCによるフレット状態送信
 * - クイックコードショートカット（C, G, D, Am）
 * - ハプティックフィードバック（navigator.vibrate）
 * - 接続ステータス表示
 */

class MobileController {
  constructor() {
    this.fretStates = [0, 0, 0, 0, 0, 0];
    this.webrtc = null;
    this.isConnected = false;
    this.stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
    this.totalFrets = 4;

    console.log('MobileController: Initialized');
  }

  handleTouch(stringIdx, fret) {
    // ハプティックフィードバック（対応ブラウザのみ）
    if (window.navigator.vibrate) {
      window.navigator.vibrate(10);
    }

    // フレット状態を更新
    this.fretStates[stringIdx] = fret;

    console.log(`MobileController: Touch - String ${this.stringNames[stringIdx]}, Fret ${fret}`);

    // WebRTCで送信
    if (this.webrtc) {
      this.webrtc.send({
        type: 'FRET_UPDATE',
        payload: this.fretStates
      });
    }

    this.updateFretDisplay();
  }

  setChord(chordPattern) {
    console.log(`MobileController: Setting chord: [${chordPattern.join(', ')}]`);
    this.fretStates = [...chordPattern];

    // WebRTCで送信
    if (this.webrtc) {
      this.webrtc.send({
        type: 'FRET_UPDATE',
        payload: this.fretStates
      });
    }

    this.updateFretDisplay();
  }

  updateFretDisplay() {
    // 全てのフレットボタンを更新
    for (let stringIdx = 0; stringIdx < 6; stringIdx++) {
      for (let fret = 0; fret <= this.totalFrets; fret++) {
        this.updateFretButton(stringIdx, fret);
      }
    }
  }

  updateFretButton(stringIdx, fret) {
    const cell = document.getElementById(`fret-${stringIdx}-${fret}`);
    if (!cell) return;

    const isActive = this.fretStates[stringIdx] === fret;

    // アクティブスタイルの設定
    cell.className = `flex-[2] flex items-center justify-center transition-all ${
      isActive
        ? 'bg-orange-500 border-orange-300 text-white scale-125 shadow-lg z-30'
        : 'active:bg-white/5 border-slate-800/50 text-slate-700 hover:bg-slate-800'
    }`;
  }

  updateConnectionStatus(connected) {
    const dot = document.getElementById('connection-dot');
    const text = document.getElementById('connection-text');

    if (connected) {
      dot.classList.remove('bg-red-500', 'animate-pulse');
      dot.classList.add('bg-green-500');
      text.textContent = 'LINKED TO PC';
      text.classList.remove('text-white', 'opacity-70');
      text.classList.add('text-green-400');
    } else {
      dot.classList.remove('bg-green-500');
      dot.classList.add('bg-red-500', 'animate-pulse');
      text.textContent = 'LINKING...';
      text.classList.remove('text-green-400');
      text.classList.add('text-white', 'opacity-70');
    }

    this.isConnected = connected;
    console.log(`MobileController: Connection status: ${connected}`);
  }

  updateRoomCode(roomId) {
    const display = document.getElementById('room-code-display');
    if (display) {
      display.textContent = roomId;
    }
  }

  render() {
    console.log('MobileController: Rendering interface...');

    // 弦名レールとフレットグリッドの生成
    const stringNamesRail = document.querySelector('.w-14.flex');
    const fretsGrid = document.querySelector('.flex-1.flex');

    if (stringNamesRail) {
      stringNamesRail.innerHTML = `
        ${this.stringNames.map(name =>
          `<div class="text-center font-black text-slate-600 text-xs italic">${name}</div>`
        ).join('')}
      `;
    }

    if (fretsGrid) {
      fretsGrid.innerHTML = '';

      for (let stringIdx = 0; stringIdx < 6; stringIdx++) {
        // Open string zone
        fretsGrid.innerHTML += this.createFretCell(stringIdx, 0);

        // Fret zones (1-4)
        for (let fret = 1; fret <= this.totalFrets; fret++) {
          fretsGrid.innerHTML += this.createFretCell(stringIdx, fret);
        }
      }

      fretsGrid.innerHTML += '</div>';
    }
  }

  createFretCell(stringIdx, fret) {
    const isActive = this.fretStates[stringIdx] === fret;
    const displayFret = fret === 0 ? 'O' : fret.toString();

    return `
      <div
        id="fret-${stringIdx}-${fret}"
        class="flex-[2] flex items-center justify-center transition-all ${
          isActive
            ? 'bg-orange-500 border-orange-300 text-white scale-125 shadow-lg z-30'
            : 'active:bg-white/5 border-slate-800/50 text-slate-700 hover:bg-slate-800'
        }"
        ontouchstart="event.preventDefault(); controller.handleTouch(${stringIdx}, ${fret})"
      >
        <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all ${
          isActive
            ? 'bg-white border-orange-400'
            : 'border-slate-800/50'
        }">
          <span class="text-xs font-black font-bold transition-all">${displayFret}</span>
        </div>
      </div>
    `;
  }

  renderChordButtons() {
    const chords = [
      { pattern: [0, 1, 0, 2, 3, 0], id: 'c-btn', name: 'C' },
      { pattern: [3, 0, 0, 0, 2, 3], id: 'g-btn', name: 'G' },
      { pattern: [2, 3, 2, 0, 0, 0], id: 'd-btn', name: 'D' },
      { pattern: [0, 1, 2, 2, 0, 0], id: 'am-btn', name: 'Am' }
    ];

    const container = document.querySelector('.grid.grid-cols-4');
    if (!container) return;

    container.innerHTML = chords.map(chord => `
      <button
        id="${chord.id}"
        onclick="controller.setChord([${chord.pattern.join(', ')}])"
        class="chord-button rounded-2xl border-2 font-black text-lg transition-all"
      >
        ${chord.name}
      </button>
    `).join('');

    // クイックコードショートカットイベントを再バインド
    chords.forEach(chord => {
      const btn = document.getElementById(chord.id);
      if (btn) {
        btn.onclick = () => controller.setChord(chord.pattern);
      }
    });
  }

  exit() {
    console.log('MobileController: Exit button pressed');
    if (this.webrtc) {
      this.webrtc.disconnect();
    }
    window.location.href = '/air-guitar-pro/';
  }
}

// グローバルインスタンスを作成
let controller;

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing MobileController...');

  // URLパラメータからルームコードを取得
  const urlParams = new URLSearchParams(window.location.search);
  const roomId = urlParams.get('room') || 'ABCD';

  // ルームコード入力フィールドに設定
  const roomInput = document.getElementById('room-code-input');
  if (roomInput) {
    roomInput.value = roomId;
  }

  // ルームコード表示を更新
  const roomCodeDisplay = document.getElementById('room-code-display');
  if (roomCodeDisplay) {
    roomCodeDisplay.textContent = roomId;
  }

  // コントローラーインスタンスを作成
  controller = new MobileController();

  // WebRTCサービスを初期化（クライアントモード）
  const webrtcService = new WebRTCService(roomId);

  // 接続イベントリスナーを設定
  webrtcService.onMessage((data) => {
    console.log('MobileController: Received message:', data);
    if (data.type === 'FRET_UPDATE') {
      controller.fretStates = data.payload;
      controller.updateFretDisplay();
    }
  });

  webrtcService.onConnected(() => {
    console.log('MobileController: Connected to PC');
    controller.updateConnectionStatus(true);
  });

  // WebRTC接続を開始
  webrtcService.initialize(false);

  // コントローラーにWebRTCサービスを設定
  controller.webrtc = webrtcService;

  // UIイベントをバインド
  const pcModeBtn = document.getElementById('pc-mode-btn');
  if (pcModeBtn) {
    pcModeBtn.onclick = () => {
      window.location.href = `/air-guitar-pro/pc/?room=${roomId}`;
    };
  }

  const exitBtn = document.getElementById('exit-btn');
  if (exitBtn) {
    exitBtn.onclick = () => controller.exit();
  }

  // グリッドをレンダリング
  controller.render();

  console.log('MobileController: Initialization complete');
});
