/**
 * WebRTC Service
 *
 * PeerJSを使用したP2P通信サービス
 *
 * 機能:
 * - PeerJS接続の初期化・管理
 * - データ送信・受信
 * - 自動再接続ロジック
 * - エラーハンドリング
 */

class WebRTCService {
  constructor(roomId) {
    this.roomId = roomId;
    this.peer = null;
    this.connection = null;
    this.onMessageCallback = null;
    this.onConnectedCallback = null;
    this.isHost = false;
    console.log(`WebRTCService initialized for room: ${roomId}`);
  }

  async initialize(isHost) {
    this.isHost = isHost;
    const peerId = isHost ? `AIR-GUITAR-PC-${this.roomId}` : undefined;

    console.log(`Initializing PeerJS. Host: ${isHost}, Peer ID: ${peerId || 'auto-generated'}`);

    this.peer = new Peer(peerId, {
      debug: 2,
      config: {
        'iceServers': [
          { 'urls': 'stun:stun.l.google.com:19302' },
          { 'urls': 'stun:stun1.l.google.com:19302' }
        ]
      }
    });

    this.peer.on('open', (id) => {
      console.log(`Peer ID is: ${id}`);
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
        console.log('Incoming connection from:', conn.peer);
      });
    }
  }

  connectToHost() {
    if (!this.peer || this.peer.destroyed) return;
    const targetId = `AIR-GUITAR-PC-${this.roomId}`;
    console.log(`Connecting to host: ${targetId}`);

    this.connection = this.peer.connect(targetId, {
      reliable: true
    });
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
    } else {
      console.warn('Cannot send: connection not open');
    }
  }

  disconnect() {
    this.connection?.close();
    this.peer?.destroy();
    console.log('WebRTC Service disconnected');
  }
}
