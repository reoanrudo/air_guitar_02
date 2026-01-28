/**
 * Lobby
 *
 * Air Guitar Proのロビー画面
 *
 * 機能:
 * - 4文字ルームコード生成
 * - PC/モバイルモード選択
 * - URLハッシュからのルームコード自動読み込み
 * - モード選択によるページ遷移
 */

class Lobby {
  constructor() {
    this.id = '';
    this.role = 'LOBBY';
    console.log('Lobby: Initialized');
  }

  generateId() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let result = '';
    for (let i = 0; i < 4; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    console.log(`Lobby: Generated room ID: ${result}`);
    return result;
  }

  handlePCMode() {
    const newId = this.id || this.generateId();
    console.log(`Lobby: PC Mode with room: ${newId}`);
    window.location.href = `/air-guitar-pro/pc/?room=${newId}`;
  }

  handleMobileMode() {
    if (this.id.length !== 4) {
      alert('Please enter a 4-character Room ID first!');
      return;
    }
    console.log(`Lobby: Mobile Mode with room: ${this.id}`);
    window.location.href = `/air-guitar-pro/mobile/?room=${this.id}`;
  }

  render() {
    console.log('Lobby: Rendering...');

    // URLハッシュからルームコードを取得
    const hash = window.location.hash.replace('#', '');
    if (hash && hash.length === 4) {
      this.id = hash.toUpperCase();
      const roomInput = document.getElementById('room-code-input');
      if (roomInput) {
        roomInput.value = this.id;
      }
    }
  }
}

// グローバルインスタンスを作成
let lobby;

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing Lobby...');

  lobby = new Lobby();
  console.log('Lobby: Initialization complete');
});
